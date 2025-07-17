
## Respaldos de versión estable

Cada vez que se declara una versión **estable** (p. ej. v3.3.26) se debe generar un respaldo general que incluya:

1. **Código fuente**: tar.gz del repositorio (`git archive --format=tar.gz -o backup_<tag>.tar.gz <tag>`).  
2. **Frontend HTML**: copia del `index.html` subido a S3 (`index_<tag>.html`) y almacenamiento en `/resultados/_respaldos/` dentro del repo.  
3. **Base de Datos**: snapshot de RDS (`aws rds create-db-snapshot --db-instance-identifier ...`).  
4. **Zip de Lambda**: guardar `lambda.zip` generado (con el número de versión).  

Esto garantiza que podamos restaurar cualquier versión estable en minutos. 