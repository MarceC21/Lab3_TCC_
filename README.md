# Laboratorio 3 - Teoría de la Computación

## Problema 1 - Árbol Sintáctico

Este programa procesa expresiones regulares utilizando el algoritmo **Shunting Yard** para convertirlas de notación **infix a postfix** y posteriormente construye su **árbol sintáctico**.

Para la construcción del árbol se utiliza un stack y objetos de tipo `Nodo`, donde los operandos forman las hojas y los operadores (`|`, `·` y `*`) forman los nodos internos.

La visualización de los árboles sintácticos se realiza utilizando la librería **Graphviz**, generando una imagen `.png` para cada expresión procesada.

El programa lee las expresiones regulares desde el archivo `expresiones.txt` y procesa cada línea individualmente.

## Estructura

```text
Problema1/
├── arboles/
│   ├── arbol_linea_1.png
│   ├── arbol_linea_2.png
│   ├── arbol_linea_3.png
│   └── arbol_linea_4.png
├── arbol_sintactico.py
└── expresiones.txt
```

## Ejecución

Para ejecutar el programa:

```bash
python arbol_sintactico.py
```

Los árboles generados se guardan automáticamente dentro de la carpeta `arboles/`.

## Video de demostración
**YouTube:** [Ver video de demostración](https://youtu.be/PDnCzI3Ld5E)
