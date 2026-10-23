# Monitor de menciones a Sergio Massa

Página web que reúne las menciones a Sergio Massa en portales de noticias nacionales y del
interior. Se publica gratis en GitHub Pages y se actualiza sola cada 15 minutos en la nube
(GitHub Actions), aunque tu computadora esté apagada. Se abre desde cualquier navegador, en la
computadora o el celular, y se comparte con el link.

## Pestañas
- **Última hora**: menciones publicadas en los últimos 60 minutos.
- **Hoy, por hora**: todo el día agrupado por franja horaria (15:00 a 15:59, etc.).
- **Menciones pasadas**: un renglón por día. Cada día tiene su propia página
  (`dia/AAAA-MM-DD.html`) con todas sus menciones ordenadas por hora, con su link para compartir.

Cada mención tiene un resumen breve, el link directo a la nota y botones para copiarlo o
compartirlo por WhatsApp. Se puede filtrar por Nacionales, Interior y Otros portales.

## Fuentes
- **Portales nacionales**: Clarín, La Nación, Infobae, Página/12, Ámbito, Perfil, TN, La Política
  Online, El Cronista, C5N, Minuto Uno.
- **Medios del interior** (RSS directo): Los Andes, Diario Uno, MDZ, Sitio Andino, La Capital
  (Rosario), La Gaceta, El Tribuno (Salta y Jujuy), Todo Jujuy, Río Negro, LM Neuquén, El Día,
  0221, 0223, InfoCielo, El Litoral (Corrientes), Época, Misiones Online, Diario Norte, Chaco Día
  por Día, Diario Panorama, El Ancasti, Tiempo de San Juan, Diario de Cuyo, Diario Huarpe, El Diario
  de la República, La Arena, El Chubut, El Sureño, Uno Entre Ríos.
- **Google Noticias**: suma el resto de los portales (incluidos los del interior sin RSS, como
  La Voz o Cadena 3). La app convierte cada link de Google en el link directo de la nota.

## Resúmenes con tu plan de Claude
Los resúmenes los escribe Claude Code usando un token de tu suscripción de Claude
(`claude setup-token`), guardado como secreto `CLAUDE_CODE_OAUTH_TOKEN` en el repositorio.
Se descuentan del uso de tu plan; no hace falta clave de API ni cambiar de plan. El modelo es
`haiku`, que gasta poco. Si se alcanza el límite del plan o el token vence (dura un año), la
página sigue funcionando con resúmenes simples (título y bajada).

## Cómo funciona
- `.github/workflows/actualizar.yml`: cada 15 minutos ejecuta `actualizar.py`, guarda las
  menciones nuevas en `datos/` (un archivo por día) y publica la carpeta `sitio/`.
- Para actualizar a mano: en GitHub, pestaña **Actions** > *Actualizar menciones* > **Run workflow**.
- Para probar en esta PC: `.venv\Scripts\python.exe actualizar.py` y abrir `sitio\index.html`.
