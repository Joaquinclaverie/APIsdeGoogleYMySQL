# APIsdeGoogleYMySQL
Esta es una aplicación para inventariar en una Base de Datos todos los archivos pertenecientes a la unidad de Google Drive de un usuario. 
La base de datos MySQL esta creada desde la aplicación. 
Dicha base almacena el nombre del archivo, la extensión, el owner del archivo, la visibilidad (público o privado) y la fecha de última modificación. 
En el caso de encontrar archivos que estén configurados como públicos y puedan ser accedidos por cualquier persona, esta aplicacion modifica dicha configuración para establecer el archivo como privado y envia un e-mail al owner notificando el cambio realizado. 
La aplicación tiene la lógica necesaria para guardar en la base sólo aquellos archivos que no hayan sido almacenados en alguna corrida anterior o actualiza la fecha de modificación o cualquier otro dato en caso de corresponder. Asimismo, mantiene un inventario histórico de todos los archivos que fueron en algún momento públicos.
