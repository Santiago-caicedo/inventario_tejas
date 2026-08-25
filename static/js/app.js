// Interacciones del sistema — Terracogua Arcillas

document.addEventListener('DOMContentLoaded', function () {

  // Cerrar mensajes
  document.querySelectorAll('.mensaje .cerrar').forEach(function (boton) {
    boton.addEventListener('click', function () {
      boton.closest('.mensaje').remove();
    });
  });

  // ----- Formulario de pedido: filas dinámicas de ítems -----
  var tabla = document.getElementById('tabla-items');
  if (!tabla) return;

  var cuerpo = tabla.querySelector('tbody');
  var plantilla = document.getElementById('plantilla-item').innerHTML;
  var totalForms = document.querySelector('input[name$="-TOTAL_FORMS"]');
  var datosProductos = {};
  var nodoDatos = document.getElementById('datos-productos');
  if (nodoDatos) datosProductos = JSON.parse(nodoDatos.textContent);

  function conectarFila(fila) {
    var select = fila.querySelector('select[name$="-producto"]');
    var precio = fila.querySelector('input[name$="-precio"]');
    if (select && precio) {
      select.addEventListener('change', function () {
        var info = datosProductos[select.value];
        if (info && (!precio.value || precio.value === '0')) {
          precio.value = info.precio;
        }
      });
    }
    var quitar = fila.querySelector('.quitar-fila');
    if (quitar) {
      quitar.addEventListener('click', function () {
        // Se marca para eliminar y se oculta: así los índices del formset
        // siguen siendo consecutivos y Django valida sin problemas.
        var borrar = fila.querySelector('input[name$="-DELETE"]');
        if (borrar) borrar.checked = true;
        fila.classList.add('oculta');
      });
    }
  }

  cuerpo.querySelectorAll('.fila-item').forEach(conectarFila);

  document.getElementById('agregar-item').addEventListener('click', function () {
    var indice = parseInt(totalForms.value, 10);
    var envoltura = document.createElement('tbody');
    envoltura.innerHTML = plantilla.replace(/__prefix__/g, indice);
    var fila = envoltura.querySelector('tr');
    cuerpo.appendChild(fila);
    totalForms.value = indice + 1;
    conectarFila(fila);
    fila.querySelector('select').focus();
  });
});
