const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class IndicesPropiedades {
    constructor() {
        this.indices = {
            ciudades: new Map(),        // ciudad -> Set<id>
            precios: new Map(),         // rango -> Set<id>
            operaciones: new Map(),     // tipo -> Set<id>
            tipos: new Map(),           // tipo_propiedad -> Set<id>
            texto: new Map(),           // palabra -> Set<id>
            propiedades: new Map(),     // id -> datos_completos
            propiedadesSinTipo: new Set() // ids de propiedades sin tipo asignado
        };
        
        this.rangosPrecios = [
            [0, 500000],
            [500000, 1000000],
            [1000000, 2000000],
            [2000000, 3000000],
            [3000000, 5000000],
            [5000000, 10000000],
            [10000000, Infinity]
        ];
        
        this.mapeoTiposPropiedad = {
            'casa': 'casa_sola',
            'casa sola': 'casa_sola',
            'departamento': 'departamento',
            'terreno': 'terreno',
            'local': 'local',
            'propiedad': 'sin_tipo',
            'casa en condominio': 'casa_condominio',
            'casa_condominio': 'casa_condominio'
        };
        
        this.mapeoInversoTipos = {
            'casa_sola': 'casa_sola',
            'departamento': 'departamento',
            'terreno': 'terreno',
            'local': 'local',
            'sin_tipo': 'sin_tipo',
            'casa_condominio': 'casa_condominio'
        };

        this.mapeoTiposOperacion = {
            'venta': 'venta',
            'renta': 'renta',
            'desconocido': 'desconocido',
            'en venta': 'venta',
            'en renta': 'renta',
            'se vende': 'venta',
            'se renta': 'renta',
            'vendida': 'venta',
            'rentada': 'renta'
        };

        this.mapeoInversoOperaciones = {
            'venta': 'venta',
            'renta': 'renta',
            'desconocido': 'desconocido'
        };
        
        this.dataPath = path.join(process.cwd(), 'resultados', 'propiedades_estructuradas.json');
        this.lastLoadTime = null;
        this.loadError = null;
        this.datosIndexados = false;
        this.ultimaModificacion = null;
        this.estadisticasCache = null;
        this.ultimoHashContenido = null;
        this.CACHE_TTL = 30 * 60 * 1000; // 30 minutos
        this.intervaloVerificacion = null;
        this.INTERVALO_VERIFICACION = 5 * 60 * 1000; // 5 minutos
        this.cacheEtag = null;
        this.cacheResultados = new Map(); // Cache para resultados de búsqueda
        this.cargandoDatos = false;
        this.colaPromesas = [];
    }

    iniciarVerificacionPeriodica() {
        if (this.intervaloVerificacion) {
            clearInterval(this.intervaloVerificacion);
        }

        this.intervaloVerificacion = setInterval(async () => {
            try {
                if (await this.necesitaRecargar()) {
                    console.log('Detectado cambio en datos, recargando índices...');
                    await this.cargarDatos(true);
                }
            } catch (error) {
                console.error('Error en verificación periódica:', error);
            }
        }, this.INTERVALO_VERIFICACION);
    }

    detenerVerificacionPeriodica() {
        if (this.intervaloVerificacion) {
            clearInterval(this.intervaloVerificacion);
            this.intervaloVerificacion = null;
        }
    }

    async necesitaRecargar() {
        try {
            if (!this.datosIndexados) return true;
            if (Date.now() - this.lastLoadTime < this.CACHE_TTL && this.datosIndexados) return false;

            const stats = await fs.stat(this.dataPath);
            const ultimaModificacion = stats.mtime.getTime();

            if (ultimaModificacion === this.ultimaModificacion && 
                Date.now() - this.lastLoadTime < this.CACHE_TTL) {
                return false;
            }

            const contenido = await fs.readFile(this.dataPath, 'utf8');
            const hashActual = crypto.createHash('md5').update(contenido).digest('hex');

            if (hashActual === this.ultimoHashContenido) {
                this.ultimaModificacion = ultimaModificacion;
                this.lastLoadTime = Date.now();
                return false;
            }

            return true;
        } catch (error) {
            console.error('Error verificando archivo:', error);
            return true;
        }
    }

    async cargarDatos(forzarRecarga = false) {
        try {
            if (this.cargandoDatos) {
                return new Promise((resolve, reject) => {
                    this.colaPromesas.push({ resolve, reject });
                });
            }

            if (!forzarRecarga && !await this.necesitaRecargar()) {
                return this.estadisticasCache;
            }

            this.cargandoDatos = true;
            console.log('Cargando datos desde:', this.dataPath);

            const contenido = await fs.readFile(this.dataPath, 'utf8');
            const hashActual = crypto.createHash('md5').update(contenido).digest('hex');

            if (!forzarRecarga && hashActual === this.ultimoHashContenido) {
                this.lastLoadTime = Date.now();
                this.cargandoDatos = false;
                return this.estadisticasCache;
            }

            const data = JSON.parse(contenido);
            if (!data || !data.propiedades || !Array.isArray(data.propiedades)) {
                throw new Error('Formato de datos inválido');
            }

            Object.values(this.indices).forEach(index => index.clear());
            this.cacheResultados.clear();

            console.log(`Indexando ${data.propiedades.length} propiedades...`);

            data.propiedades.forEach((propiedad, id) => {
                this.indices.propiedades.set(id, propiedad);

                if (propiedad.ubicacion?.ciudad) {
                    const ciudad = propiedad.ubicacion.ciudad.toLowerCase();
                    if (!this.indices.ciudades.has(ciudad)) {
                        this.indices.ciudades.set(ciudad, new Set());
                    }
                    this.indices.ciudades.get(ciudad).add(id);
                }

                const precio = propiedad.propiedad?.precio?.valor || 0;
                const rangoPrecio = this.obtenerRangoPrecio(precio);
                if (!this.indices.precios.has(rangoPrecio)) {
                    this.indices.precios.set(rangoPrecio, new Set());
                }
                this.indices.precios.get(rangoPrecio).add(id);

                if (propiedad.propiedad?.tipo_operacion) {
                    const operacionOriginal = propiedad.propiedad.tipo_operacion.toLowerCase();
                    const operacion = this.mapeoTiposOperacion[operacionOriginal] || 'desconocido';
                    if (!this.indices.operaciones.has(operacion)) {
                        this.indices.operaciones.set(operacion, new Set());
                    }
                    this.indices.operaciones.get(operacion).add(id);
                } else {
                    if (!this.indices.operaciones.has('desconocido')) {
                        this.indices.operaciones.set('desconocido', new Set());
                    }
                    this.indices.operaciones.get('desconocido').add(id);
                }

                if (propiedad.propiedad?.tipo_propiedad) {
                    const tipoOriginal = propiedad.propiedad.tipo_propiedad.toLowerCase();
                    const tipo = this.mapeoTiposPropiedad[tipoOriginal] || 'sin_tipo';
                    if (!this.indices.tipos.has(tipo)) {
                        this.indices.tipos.set(tipo, new Set());
                    }
                    this.indices.tipos.get(tipo).add(id);
                } else {
                    this.indices.propiedadesSinTipo.add(id);
                    if (!this.indices.tipos.has('sin_tipo')) {
                        this.indices.tipos.set('sin_tipo', new Set());
                    }
                    this.indices.tipos.get('sin_tipo').add(id);
                }

                const textosBusqueda = [
                    propiedad.ubicacion?.direccion_completa,
                    propiedad.descripcion_original,
                    propiedad.ubicacion?.ciudad,
                    propiedad.propiedad?.tipo_propiedad
                ].filter(Boolean).join(' ').toLowerCase();

                const palabras = textosBusqueda.split(/\W+/).filter(p => p.length > 2);
                palabras.forEach(palabra => {
                    if (!this.indices.texto.has(palabra)) {
                        this.indices.texto.set(palabra, new Set());
                    }
                    this.indices.texto.get(palabra).add(id);
                });
            });

            this.ultimoHashContenido = hashActual;
            this.ultimaModificacion = (await fs.stat(this.dataPath)).mtime.getTime();
            this.lastLoadTime = Date.now();
            this.datosIndexados = true;
            this.loadError = null;
            this.estadisticasCache = this.generarEstadisticas();

            console.log('Indexación completada:', this.estadisticasCache);

            // Resolver promesas pendientes
            this.colaPromesas.forEach(({ resolve }) => resolve(this.estadisticasCache));
            this.colaPromesas = [];

            this.cargandoDatos = false;
            return this.estadisticasCache;

        } catch (error) {
            this.loadError = error;
            console.error('Error cargando datos:', error);
            
            // Rechazar promesas pendientes
            this.colaPromesas.forEach(({ reject }) => reject(error));
            this.colaPromesas = [];
            
            this.cargandoDatos = false;
            throw error;
        }
    }

    buscar({ ciudad, tipoPropiedad, tipoOperacion }) {
        const resultados = [];
        const propiedades = Array.from(this.indices.propiedades.entries());

        propiedades.forEach(([id, propiedad]) => {
            let cumpleFiltros = true;

            if (ciudad && ciudad !== 'todas') {
                const ciudadPropiedad = propiedad.ubicacion?.ciudad?.toLowerCase();
                if (!ciudadPropiedad || ciudadPropiedad !== ciudad.toLowerCase()) {
                    cumpleFiltros = false;
                }
            }

            if (tipoPropiedad && tipoPropiedad !== 'todos') {
                const tipoOriginal = propiedad.propiedad?.tipo_propiedad?.toLowerCase();
                const tipo = this.mapeoTiposPropiedad[tipoOriginal] || 'sin_tipo';
                if (tipo !== tipoPropiedad) {
                    cumpleFiltros = false;
                }
            }

            if (tipoOperacion && tipoOperacion !== 'todas') {
                const operacionOriginal = propiedad.propiedad?.tipo_operacion?.toLowerCase();
                const operacion = this.mapeoTiposOperacion[operacionOriginal] || 'desconocido';
                if (operacion !== tipoOperacion) {
                    cumpleFiltros = false;
                }
            }

            if (cumpleFiltros) {
                resultados.push(propiedad);
            }
        });

        return resultados;
    }

    generarEstadisticas() {
        const estadisticas = {
            totalPropiedades: this.indices.propiedades.size,
            ciudades: [],
            tiposPropiedad: [],
            tiposOperacion: [],
            validacion: {
                totalPorTipo: 0,
                totalPorOperacion: 0,
                totalPorCiudad: 0,
                propiedadesSinTipo: this.indices.propiedadesSinTipo.size,
                integridadTipos: false,
                integridadOperaciones: false,
                integridadCiudades: false
            }
        };

        // Ciudades
        for (const [ciudad, propiedades] of this.indices.ciudades) {
            estadisticas.ciudades.push({
                nombre: ciudad,
                total: propiedades.size
            });
        }
        estadisticas.ciudades.sort((a, b) => b.total - a.total);

        // Tipos de propiedad
        for (const [tipo, propiedades] of this.indices.tipos) {
            if (tipo !== 'sin_tipo') {
                estadisticas.tiposPropiedad.push({
                    nombre: tipo,
                    total: propiedades.size
                });
                estadisticas.validacion.totalPorTipo += propiedades.size;
            }
        }
        estadisticas.tiposPropiedad.sort((a, b) => b.total - a.total);

        // Tipos de operación
        for (const [operacion, propiedades] of this.indices.operaciones) {
            estadisticas.tiposOperacion.push({
                nombre: operacion,
                total: propiedades.size
            });
            estadisticas.validacion.totalPorOperacion += propiedades.size;
        }
        estadisticas.tiposOperacion.sort((a, b) => b.total - a.total);

        // Validación de integridad
        estadisticas.validacion.totalPorCiudad = Array.from(this.indices.ciudades.values())
            .reduce((total, propiedades) => total + propiedades.size, 0);

        estadisticas.validacion.integridadTipos = 
            estadisticas.validacion.totalPorTipo + this.indices.propiedadesSinTipo.size === this.indices.propiedades.size;

        estadisticas.validacion.integridadOperaciones = 
            estadisticas.validacion.totalPorOperacion === this.indices.propiedades.size;

        estadisticas.validacion.integridadCiudades = 
            estadisticas.validacion.totalPorCiudad === this.indices.propiedades.size;

        return estadisticas;
    }

    interseccion(set1, set2) {
        return new Set([...set1].filter(x => set2.has(x)));
    }

    obtenerRangoPrecio(precio) {
        for (const [min, max] of this.rangosPrecios) {
            if (precio >= min && precio < max) {
                return `${min}-${max}`;
            }
        }
        return 'sin-precio';
    }
}

module.exports = IndicesPropiedades; 