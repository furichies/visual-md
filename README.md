# visual-md

Aplicación de escritorio GTK3 para ver y editar ficheros de texto plano o
Markdown en una ventana translúcida, movible y siempre por encima de las demás.

## Características

- Ventana GTK3 con opacidad ajustable (72 % por defecto).
- La ventana se puede mover desde la barra de título.
- Se mantiene por encima de las demás ventanas.
- Abrir, guardar, guardar como y recargar ficheros.
- Edición de texto con copiar, pegar y copiar todo.
- Fuente monoespaciada y texto claro.
- Atajos de teclado para todas las operaciones.
- Integración con el escritorio mediante lanzador e icono.
- Paquete `.deb` instalable para todos los usuarios.

## Requisitos

- Linux con GTK3 y PyGObject.
- Sesión X11 para la opacidad y la función de mantener la ventana encima.
- Un compositor: GNOME/Mutter ya lo incluye; en un WM sin compositor se puede
  usar `picom`.

Dependencias Debian:

```bash
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

## Instalación

Paquete incluido en el repositorio:

```bash
sudo apt install ./dist/visual-md_0.1.0_all.deb
```

El paquete instala:

```text
/usr/bin/visual-md
/usr/share/applications/visual-md.desktop
/usr/share/icons/hicolor/scalable/apps/visual-md.svg
/usr/share/man/man1/visual-md.1.gz
/usr/share/doc/visual-md/
```

También se puede ejecutar desde el código fuente:

```bash
python3 visual-md.py fichero.md
```

## Uso

```bash
visual-md fichero.md
```

Sin argumento abre una ventana vacía. `Ctrl+O` permite abrir un fichero.

## Atajos

| Atajo | Acción |
|---|---|
| `Ctrl+O` | Abrir fichero |
| `Ctrl+S` | Guardar |
| `Ctrl+Shift+S` | Guardar como |
| `Ctrl+R` | Recargar |
| `Ctrl+Q` | Salir |
| `Ctrl` + `+` | Aumentar opacidad |
| `Ctrl` + `-` | Reducir opacidad |
| `Ctrl+C` / `Ctrl+V` | Copiar / pegar |

La barra de título incluye botones para abrir, guardar, copiar todo y recargar.

## Construir el paquete

```bash
dpkg-buildpackage -us -uc -b
```

El `.deb` se genera en el directorio padre. El empaquetado Debian está en
`debian/`.

## Estructura

```text
visual-md/
├── visual-md.py
├── README.md
├── LICENSE
├── ejemplo.md
├── visual-md.desktop
├── debian/
└── dist/
    └── visual-md_0.1.0_all.deb
```

## Licencia

MIT. Consulta `LICENSE`.
