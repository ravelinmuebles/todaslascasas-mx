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
        
        // Mapeo inverso para devolver el tipo correcto
        this.mapeoInversoTipos = {
            'casa_sola': 'casa_sola',
            'departamento': 'departamento',
            'terreno': 'terreno',
            'local': 'local',
            'sin_tipo': 'sin_tipo',
            'casa_condominio': 'casa_condominio'
        };

        // Mapeo de tipos de operación
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

        // Mapeo inverso de operaciones
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
            // Si los datos nunca se han cargado
            if (!this.datosIndexados) {
                return true;
            }

            // Si el caché no ha expirado y tenemos datos
            if (Date.now() - this.lastLoadTime < this.CACHE_TTL && this.datosIndexados) {
                return false;
            }

            // Verificar modificación del archivo
            const stats = await fs.stat(this.dataPath);
            const ultimaModificacion = stats.mtime.getTime();

            // Si el archivo no ha cambiado y el caché no ha expirado
            if (ultimaModificacion === this.ultimaModificacion && 
                Date.now() - this.lastLoadTime < this.CACHE_TTL) {
                return false;
            }

            // Si el archivo ha cambiado, verificar el contenido
            const contenido = await fs.readFile(this.dataPath, 'utf8');
            const hashActual = crypto.createHash('md5').update(contenido).digest('hex');

            // Si el contenido no ha cambiado
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
            // Si ya hay una carga en progreso, esperar a que termine
            if (this.cargandoDatos) {
                return new Promise((resolve, reject) => {
                    this.colaPromesas.push({ resolve, reject });
                });
            }

            // Verificar si necesitamos recargar
            if (!forzarRecarga && !await this.necesitaRecargar()) {
                return this.estadisticasCache;
            }

            this.cargandoDatos = true;
            console.log('Cargando datos desde:', this.dataPath);

            const contenido = await fs.readFile(this.dataPath, 'utf8');
            const hashActual = crypto.createHash('md5').update(contenido).digest('hex');

            // Si el contenido no ha cambiado y no es forzado
            if (!forzarRecarga && hashActual === this.ultimoHashContenido) {
                this.lastLoadTime = Date.now();
                this.cargandoDatos = false;
                return this.estadisticasCache;
            }

            const data = JSON.parse(contenido);
            if (!data || !data.propiedades || !Array.isArray(data.propiedades)) {
                throw new Error('Formato de datos inválido');
            }

            // Limpiar índices existentes
            Object.values(this.indices).forEach(index => index.clear());
            this.cacheResultados.clear();

            console.log(`Indexando ${data.propiedades.length} propiedades...`);

            // Indexar propiedades
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

            // Actualizar metadatos
            this.ultimoHashContenido = hashActual;
            this.ultimaModificacion = (await fs.stat(this.dataPath)).mtime.getTime();
            this.lastLoadTime = Date.now();
            this.loadError = null;
            this.datosIndexados = true;
            
            // Generar y cachear estadísticas
            this.estadisticasCache = this.generarEstadisticas();
            this.cacheEtag = this.ultimoHashContenido;

            console.log('Indexación completada:', this.estadisticasCache);

            // Resolver promesas pendientes
            this.colaPromesas.forEach(({ resolve }) => resolve(this.estadisticasCache));
            this.colaPromesas = [];
            this.cargandoDatos = false;

            return this.estadisticasCache;

        } catch (error) {
            this.loadError = error;
            console.error('Error al cargar/indexar datos:', error);
            
            // Rechazar promesas pendientes
            this.colaPromesas.forEach(({ reject }) => reject(error));
            this.colaPromesas = [];
            this.cargandoDatos = false;
            
            throw error;
        }
    }

    buscar({ ciudad, precioMin, precioMax, tipoOperacion, tipoPropiedad, busqueda, page = 1, limit = 20 }) {
        try {
            let resultados = null;
        let primerFiltro = true;

        // Filtrar por ciudad
        if (ciudad) {
                const propiedadesCiudad = this.indices.ciudades.get(ciudad);
                resultados = propiedadesCiudad ? new Set(propiedadesCiudad) : new Set();
                primerFiltro = false;
            }

            // Filtrar por rango de precios
            if ((precioMin !== null && precioMin !== undefined) || 
                (precioMax !== null && precioMax !== undefined)) {
                const propiedadesPrecio = new Set();
                this.indices.precios.forEach((propiedades, rango) => {
                    const [min, max] = rango.split('-').map(Number);
                    if ((!precioMin || min >= precioMin) && (!precioMax || min <= precioMax)) {
                        propiedades.forEach(id => propiedadesPrecio.add(id));
                }
            });
                resultados = primerFiltro ? propiedadesPrecio : this.interseccion(resultados, propiedadesPrecio);
                primerFiltro = false;
        }

        // Filtrar por tipo de operación
        if (tipoOperacion) {
                const operacionNormalizada = tipoOperacion.toLowerCase();
                const operacionMapeada = this.mapeoTiposOperacion[operacionNormalizada] || operacionNormalizada;
                const propiedadesOperacion = this.indices.operaciones.get(operacionMapeada);
                if (propiedadesOperacion) {
                    resultados = primerFiltro ? new Set(propiedadesOperacion) : this.interseccion(resultados, propiedadesOperacion);
                primerFiltro = false;
                } else {
                    return { propiedades: [], total: 0, pagina: page, limite: limit };
            }
        }

        // Filtrar por tipo de propiedad
        if (tipoPropiedad) {
            const tipos = Array.isArray(tipoPropiedad) ? tipoPropiedad : [tipoPropiedad];
            const propiedadesTipo = new Set();
            
            tipos.forEach(tipo => {
                const tipoLower = tipo.toLowerCase();
                    const tipoMapeado = this.mapeoTiposPropiedad[tipoLower] || tipoLower;
                    if (this.indices.tipos.has(tipoMapeado)) {
                        this.indices.tipos.get(tipoMapeado).forEach(id => propiedadesTipo.add(id));
                }
            });
            
            if (propiedadesTipo.size > 0) {
                    resultados = primerFiltro ? propiedadesTipo : this.interseccion(resultados, propiedadesTipo);
                primerFiltro = false;
                } else {
                    return { propiedades: [], total: 0, pagina: page, limite: limit };
                }
        }

        // Filtrar por texto de búsqueda
        if (busqueda) {
            const palabras = busqueda.toLowerCase().split(/\W+/).filter(p => p.length > 2);
            if (palabras.length > 0) {
                const propiedadesTexto = new Set();
                    let primeraInterseccion = true;
                    
                palabras.forEach(palabra => {
                        const propiedadesPalabra = this.indices.texto.get(palabra);
                        if (propiedadesPalabra) {
                            if (primeraInterseccion) {
                                propiedadesPalabra.forEach(id => propiedadesTexto.add(id));
                                primeraInterseccion = false;
                            } else {
                                const temp = new Set();
                                propiedadesPalabra.forEach(id => {
                                    if (propiedadesTexto.has(id)) temp.add(id);
                                });
                                propiedadesTexto.clear();
                                temp.forEach(id => propiedadesTexto.add(id));
                            }
                    }
                });
                    
                    if (propiedadesTexto.size > 0) {
                        resultados = primerFiltro ? propiedadesTexto : this.interseccion(resultados, propiedadesTexto);
                primerFiltro = false;
                    }
            }
        }

            // Si no hay filtros, usar todas las propiedades
        if (primerFiltro) {
            resultados = new Set(this.indices.propiedades.keys());
        }

            // Convertir resultados a array y paginar
            const propiedadesArray = Array.from(resultados).map(id => {
                const propiedad = this.indices.propiedades.get(id);
                // Mapear tipos de propiedad y operación a sus valores normalizados
                if (propiedad.propiedad) {
                    if (propiedad.propiedad.tipo_propiedad) {
                        const tipoOriginal = propiedad.propiedad.tipo_propiedad.toLowerCase();
                        propiedad.propiedad.tipo_propiedad = this.mapeoTiposPropiedad[tipoOriginal] || 'sin_tipo';
                    }
                    if (propiedad.propiedad.tipo_operacion) {
                        const operacionOriginal = propiedad.propiedad.tipo_operacion.toLowerCase();
                        propiedad.propiedad.tipo_operacion = this.mapeoTiposOperacion[operacionOriginal] || 'desconocido';
                    }
                }
                return propiedad;
            });

        const inicio = (page - 1) * limit;
        const fin = inicio + limit;
            const propiedadesPaginadas = propiedadesArray.slice(inicio, fin);

            return {
            propiedades: propiedadesPaginadas,
            total: propiedadesArray.length,
            pagina: page,
                limite: limit
            };

        } catch (error) {
            console.error('Error en búsqueda:', error);
            throw error;
        }
    }

    generarEstadisticas() {
        const stats = {
            totalPropiedades: this.indices.propiedades.size,
            ciudades: Array.from(this.indices.ciudades.entries()).map(([nombre, ids]) => ({
                nombre,
                total: ids.size
            })).sort((a, b) => b.total - a.total),
            tiposPropiedad: Array.from(this.indices.tipos.entries()).map(([nombre, ids]) => ({
                nombre,
                total: ids.size
            })).sort((a, b) => b.total - a.total),
            tiposOperacion: Array.from(this.indices.operaciones.entries()).map(([nombre, ids]) => ({
                nombre,
                total: ids.size
            })).sort((a, b) => b.total - a.total)
        };

        // Agregar propiedades sin tipo a las estadísticas
        if (this.indices.propiedadesSinTipo.size > 0) {
            stats.tiposPropiedad.push({
                nombre: 'sin_tipo',
                total: this.indices.propiedadesSinTipo.size
            });
        }

        // Validar totales
        const totalPorTipo = stats.tiposPropiedad.reduce((sum, tipo) => sum + tipo.total, 0);
        const totalPorOperacion = stats.tiposOperacion.reduce((sum, op) => sum + op.total, 0);
        const totalPorCiudad = stats.ciudades.reduce((sum, ciudad) => sum + ciudad.total, 0);

        // Agregar métricas de validación
        stats.validacion = {
            totalPorTipo,
            totalPorOperacion,
            totalPorCiudad,
            propiedadesSinTipo: this.indices.propiedadesSinTipo.size,
            integridadTipos: totalPorTipo === stats.totalPropiedades,
            integridadOperaciones: totalPorOperacion === stats.totalPropiedades,
            integridadCiudades: totalPorCiudad === stats.totalPropiedades
        };

        return stats;
    }

    interseccion(set1, set2) {
        return new Set([...set1].filter(x => set2.has(x)));
    }

    obtenerRangoPrecio(precio) {
        if (!precio || precio <= 0) return '0-0';
        for (const [min, max] of this.rangosPrecios) {
            if (precio <= max) {
                return `${min}-${max}`;
            }
        }
        return `${this.rangosPrecios[this.rangosPrecios.length - 1][0]}-Infinity`;
    }
}

module.exports = IndicesPropiedades; 