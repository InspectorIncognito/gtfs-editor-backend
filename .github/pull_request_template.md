<!-- Para una versión en inglés de esta plantilla, añade &template=pull_request_template_en.md a la URL -->

<!-- Título del PR: Utiliza el formato de Conventional Commits -->
<!-- Ejemplo: feat(EDD-0000): descripción breve del cambio -->

# 📚 Contexto

<!-- Proporciona una descripción general breve del propósito de este PR. Indica claramente qué problema aborda o qué funcionalidad agrega/cambia. Incluye enlaces a tickets de Jira, problemas o documentación relevante, si aplica. -->

# 📝 Cambios

<!-- Detalla los cambios específicos realizados en este PR. Puedes organizarlos por capas para mayor claridad. -->

- [ ] Breve descripción del cambio 1.
- [ ] Breve descripción del cambio 2.
- [ ] Breve descripción del cambio 3.

# 🔍 Qué probar

<!-- ¿Qué hay que probar para validar el PR? Más importante si el PR es a Producción y se puede revisar en Desarrollo -->

## 📸 Demostración

<!-- Incluye capturas de pantalla, GIFs o grabaciones de pantalla que muestren los cambios realizados en este PR. Asegúrate de destacar los aspectos clave de las modificaciones. -->

<!-- # 📌 Pendiente -->
<!-- Puedes incluir elementos adicionales en la lista de verificación que los colaboradores deben completar antes de que este PR pueda considerarse listo. -->

# ✅ **Criterios para aprobación**

Para que este PR sea aprobado, se debe cumplir con los siguientes puntos:

- [ ] **Aprobación del equipo backend**:
  - El PR debe ser aprobado por al menos **dos miembros** del equipo de backend.
  - Dependiendo del caso, es posible que se necesite la aprobación miembros de otros equipos.
- [ ] **Título del PR en formato Conventional Commits**
- [ ] **Cumple la funcionalidad propuesta**: El PR resuelve correctamente el problema o agrega la funcionalidad indicada en el contexto.
- [ ] **Sigue las convenciones de arquitectura del equipo**:
  - El código respeta los principios de Django-Styleguide.
  - Si es un Endpoint utiliza Django-DRF, etc.
- [ ] **Pasa las verificaciones técnicas**:
  - Todos los tests se ejecutan correctamente.
  - No genera errores en el analyzer de lint. _(Coming soon)_
- [ ] **Incluye tests adecuados**: Se han agregado pruebas, al menos para los casos borde de la funcionalidad desarrollada.
- [ ] **Documentación**: Si es una nueva funcionalidad, esta ha sido documentada según los estándares del equipo.
  - Si es un endpoint de Teléfono, éste debe de estar documentado en su respectivo Confluence.
- [ ] **Calidad textual**: No hay errores de redacción ni sintaxis en los textos agregados o modificados en el código.
- [ ] **Verificación de la capa de presentación**:
  - Si se modifica la capa de presentación, el PR a producción debe ser asignado al equipo de diseño para su revisión.
  - En la mayoría de los casos, utilizando el ambiente de Desarrollo para validar el diseño.
- [ ] **Formato del código**:
  - El código debe seguir las convenciones de formato de PEP-8