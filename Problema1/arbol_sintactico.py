r"""
Algoritmo Shunting Yard aplicado a expresiones regulares y para dibujar un árbol sintáctico

Primero válida que la expresion en formato infix este bien formada y luego la convierte a notacion postfix.
 
Reglas a tomar en cuenta:
  1. Paréntesis balanceados (con un Stack).
  2. El unico operador infijo es '|'; debe tener operandos válidos a ambos
     lados.
  3. Los operadores postfix (*, +, ?) deben ir despúes de un operando
     o de un ')'.
  4. No debe haber operadores repetidos incorrectamente (a||b, a|*b, a(**)
     con parentesis vacio, etc)
  5. La concatenación implicita debe ser válida: se inserta un operador de
     concatenación explicito entre dos tokens cuando el primero no es '(',
     el segundo no es ')' ni un operador infijo/postfix, y el primero no es
     ya un operador infijo.
  6. Caracteres escapados con '\': cualquier caracter que venga despúes de
     una '\' se trata siempre como literal/operando, sin importar si ese
     caracter normalmente seria un operador (\+, \*, \(, \., etc). Una '\'
     al final de la expresión, sin caracter siguiente, es un error.
  7. Las "extensiones" de la regex básica ('+' Y '?') se EXPANDEN
     a los operadores basicos (|, concatenacion, *) antes de correr
     Shunting Yard, ya que este solo necesita conocer esto:
         a+        ->  (a)(a)*
         a?        ->  (a|ε)
    NOTA : Se usa 'ε' como operando especial para representar la opción del vacío.
  8. Para que no haya mucho problema, la concatenación implicita se marca internamente con el simbolo CONCAT = '·', dejando el '.' libre para funcionar como operando normal.


"""
import os

# Libreria Graphviz
from graphviz import Digraph 

# Tipos de token
NONE = "INICIO"
OPERANDO = "OPERANDO"
ABRE = "ABRE_PARENTESIS"
CIERRA = "CIERRA_PARENTESIS"
INFIJO = "OPERADOR_INFIJO"      # solo '|'
POSTFIX = "OPERADOR_POSTFIX"    # '*', '+', '?'
CONCAT_TIPO = "OPERADOR_CONCAT"

OPERADORES_INFIJOS = {"|"}
OPERADORES_POSTFIX_SIMPLES = {"*", "+", "?"}

CONCAT = "\u00B7"   # simbolo interno de concatenacion, no choca con '.' literal
EPSILON = "ε"     # representa la cadena vacia (para expandir '?')


# 1) TOKENIZAR
def tokenizar(expr):
    tokens = []
    i = 0
    n = len(expr)

    while i < n:
        c = expr[i]

        #Por si hay espacio
        if c.isspace():
            i += 1
            continue

        # --- Caracter escapado con '\' ---
        if c == "\\":
            if i + 1 >= n:
                raise ValueError(
                    f"Barra invertida '\\' en la posicion {i} no tiene "
                    "un caracter siguiente para escapar"
                )
            tokens.append(expr[i:i + 2])   # ej: '\+', '\.', '\('
            i += 2
            continue

        # --- Clase de caracteres [ ... ] ---
        if c == "[":
            j = expr.find("]", i)
            if j == -1:
                raise ValueError(f"'[' en la posicion {i} no tiene ']' que lo cierre")
            tokens.append(expr[i:j + 1])
            i = j + 1
            continue

        tokens.append(c)
        i += 1

    return tokens


def clasificar(token):
    if token == "(":
        return ABRE
    if token == ")":
        return CIERRA
    if token == CONCAT:
        return CONCAT_TIPO
    if token in OPERADORES_INFIJOS:
        return INFIJO
    if token in OPERADORES_POSTFIX_SIMPLES:
        return POSTFIX
    if token.startswith("[") and token.endswith("]"):
        return OPERANDO
    if token.startswith("\\") and len(token) == 2:
        return OPERANDO       # caracter escapado 
    return OPERANDO           # letras, digitos, '.', epsilón, etc.


# 2) VALIDACIÓN

def validar_expresion(tokens):
    tipo_anterior = NONE
    error = None
    balanceada = True
    pila_parens = 0

    if len(tokens) == 0:
        return False, "La expresión esta vacia"

    for idx, token in enumerate(tokens):
        tipo = clasificar(token)

        if tipo == ABRE:
            pila_parens += 1

        elif tipo == CIERRA:
            if pila_parens == 0:
                balanceada = False
                if error is None:
                    error = f"')' en la posición {idx} no tiene '(' que la abra"
                break
            if tipo_anterior in (ABRE, INFIJO, NONE):
                if error is None:
                    error = (
                        f"')' en la posición {idx} cierra un grupo vacio o mal formado (falta un operando antes)"
                    )
            pila_parens -= 1

        elif tipo == INFIJO:
            if tipo_anterior not in (OPERANDO, CIERRA, POSTFIX):
                if error is None:
                    error = (
                        f"'{token}' en la posición {idx} no tiene operando válido a su izquierda"
                    )

        elif tipo == POSTFIX:
            if tipo_anterior not in (OPERANDO, CIERRA, POSTFIX):
                if error is None:
                    error = (
                        f"'{token}' en la posición {idx} debe ir despúes de un operando o de ')'"
                    )

        tipo_anterior = tipo

    if pila_parens != 0:
        balanceada = False
        if error is None:
            error = f"Quedaron {pila_parens} paréntesis '(' sin cerrar"

    if tipo_anterior == INFIJO and error is None:
        error = "La expresión termina en un operador infijo sin operando derecho"
    if tipo_anterior == ABRE and error is None:
        error = "La expresión termina con un '(' sin cerrar"

    primer_tipo = clasificar(tokens[0])
    if primer_tipo in (INFIJO, POSTFIX, CIERRA) and error is None:
        error = f"La expresión no puede empezar con '{tokens[0]}'"

    valida = balanceada and (error is None)
    return valida, error


# 3) EXPANSIÓN DE EXTENSIONES
# Convierte los operadores extendidos (+, ?) a la expresión regular básica utilizando únicamente concatenación, unión (|) y cerradura de Kleene (*).

def _extraer_ultimo_atomo(salida):

    if not salida:
        raise ValueError("Operador postfix sin operando válido a la izquierda")

    if salida[-1] == ")":
        balance = 0
        j = len(salida) - 1
        while j >= 0:
            if salida[j] == ")":
                balance += 1
            elif salida[j] == "(":
                balance -= 1
                if balance == 0:
                    break
            j -= 1
        if j < 0:
            raise ValueError("Paréntesis desbalanceados al expandir extension")
        return salida[j:], salida[:j]

    return [salida[-1]], salida[:-1]


def expandir_extensiones(tokens):
    """
    Recorre los tokens y expande '+' y '?'  usando solo '|', '(' ')'
    y '*'. Devuelve (tokens_expandidos, pasos) donde `pasos` describe cada expansión realizada, en orden.
    """
    salida = []
    pasos = []

    for token in tokens:
        tipo = clasificar(token)

        # Para el +
        if token == "+":
            atomo, resto = _extraer_ultimo_atomo(salida)
            expandido = ["("] + atomo + [")"] + ["("] + atomo + [")"] + ["*"]
            salida = resto + expandido
            pasos.append(
                f"Expando '+' sobre {''.join(atomo)}  ->  "
                f"({''.join(atomo)})({''.join(atomo)})*"
            )

        #Para el ?
        elif token == "?":
            atomo, resto = _extraer_ultimo_atomo(salida)
            expandido = ["("] + atomo + ["|"] + [EPSILON] + [")"]
            salida = resto + expandido
            pasos.append(
                f"Expando '?' sobre {''.join(atomo)}  ->  "
                f"({''.join(atomo)}|{EPSILON})"
            )

        else:
            salida.append(token)

    if not pasos:
        pasos.append("(no hay extensiones '+' ni  '?' que expandir)")

    return salida, pasos


# 4) INSERTAR CONCATENACIÓN EXPLICITA  
def insertar_concatenacion(tokens):
    if not tokens:
        return tokens

    con_concat = [tokens[0]]

    for i in range(len(tokens) - 1):
        actual = tokens[i]
        siguiente = tokens[i + 1]
        tipo_actual = clasificar(actual)
        tipo_siguiente = clasificar(siguiente)

        necesita_concat = (
            actual != "(" and
            tipo_siguiente != CIERRA and
            tipo_siguiente not in (INFIJO, POSTFIX) and
            tipo_actual != INFIJO
        )

        if necesita_concat:
            con_concat.append(CONCAT)
        con_concat.append(siguiente)

    return con_concat

# 5) SHUNTING YARD 
PRECEDENCIA = {
    "|": 1,
    CONCAT: 2,
    "*": 3,
}

def precedencia(token):
    return PRECEDENCIA.get(token, 0)


def infix_a_postfix(tokens_formateados):
    """
    Aplica el algoritmo Shunting Yard sobre tokens que YA tienen la
    concatenación insertada y las extensiones expandidas
    Devuelve (postfix_tokens, pasos).
    """

    # Stack 
    pila = []

    salida = []
    pasos = []

    for token in tokens_formateados:
        tipo = clasificar(token)

        if tipo == ABRE:
            pila.append(token)
            pasos.append(f"Leo '(' -> APILAR              | pila: {pila}")

        elif tipo == CIERRA:
            while pila and pila[-1] != "(":
                salida.append(pila.pop())
            pila.pop()  # descarta el '('
            pasos.append(
                f"Leo ')' -> DESAPILAR hasta '('   | salida: {''.join(salida)} | pila: {pila}"
            )

        elif token == CONCAT or tipo in (INFIJO, POSTFIX):
            while pila and pila[-1] != "(" and precedencia(pila[-1]) >= precedencia(token):
                salida.append(pila.pop())
            pila.append(token)
            simbolo = "concat" if token == CONCAT else token
            pasos.append(
                f"Leo '{simbolo}' -> saco mayor/igual precedencia, apilo | "
                f"salida: {''.join(salida)} | pila: {pila}"
            )

        else:  # OPERANDO
            salida.append(token)
            pasos.append(f"Leo '{token}' -> ENVIAR A SALIDA      | salida: {''.join(salida)}")

    while pila:
        salida.append(pila.pop())
    pasos.append(f"Fin de expresion -> vacio la pila | salida final: {''.join(salida)}")

    return salida, pasos


# 7) ARBOL SINTÁCTICO A PARTIR DEL POSTFIX
# Se recorre la lista postfix con OTRo stack, distinto del que uso en Shunting Yard
# Cada operando se mete al stack como un nodo hoja. 
# Cada operador saca del stack cantidad de nodos que necesita como hijos, 
# arma un nodo nuevo con esos hijos y lo vuelve a meter al stack
# Al terminar, debe quedar EXACTAMENTE un nodo: la raiz (root).

# En el postfix solo pueden aparecer:
#   - operandos (letras, '.', clases [...], escapados \x, o 'ε')
#   - '|'      -> operador BINARIO (saca 2 nodos: derecho, izquierdo)
#   - CONCAT   -> operador BINARIO (saca 2 nodos: derecho, izquierdo)
#   - '*'      -> operador UNARIO  (saca 1 nodo: su unico hijo)


# Esta clase es para representar un nodo
# Tiene el valor y sus hijos
class Nodo:
    def __init__(self, valor, izquierdo=None, derecho=None):
        self.valor = valor
        self.izquierdo = izquierdo
        self.derecho = derecho

    def __repr__(self):
        return f"Nodo({self.valor!r})"


# Recorre el posti¿fix de isquierda a derecha con el stack 
def construir_arbol(postfix_tokens):

    stack = []

    for token in postfix_tokens:
        tipo = clasificar(token)

        if token == CONCAT or tipo == INFIJO:
            # Operador binario ('|' o concatenacion): saco 2 y armo el nodo
            if len(stack) < 2:
                raise ValueError(
                    f"Postfix inválido: '{token}' es binario pero la pila tiene menos de 2 nodos"
                )
            derecho = stack.pop()
            izquierdo = stack.pop()
            stack.append(Nodo(token, izquierdo=izquierdo, derecho=derecho))

        elif tipo == POSTFIX:
            # Operador '*', solo un hijo
            if not stack:
                raise ValueError(
                    f"Postfix inválido: '{token}' es unario pero la pila esta vacia"
                )
            hijo = stack.pop()
            stack.append(Nodo(token, izquierdo=hijo))

        else:
            # Operando -> nodo hoja
            stack.append(Nodo(token))

    if len(stack) != 1:
        raise ValueError(
            f"Postfix inválido: al terminar deberia quedar 1 nodo en la pila y quedaron {len(stack)}"
        )

    return stack[0]

# Para dibujar
ETIQUETAS = {
    CONCAT: "·",
    "|": "|",
    "*": "*",
}


def dibujar_arbol(raiz, ruta_salida):
    """
    Dibuja el arbol sintactico con Graphviz (los nodos y las conexiones
    padre->hijo se declaran nada mas; Graphviz calcula el layout solo) y
    lo guarda como PNG en `ruta_salida` (sin extension).
    """

    dot = Digraph()
    dot.attr("node", shape="circle", fontname="Helvetica")
    contador = [0]

    def agregar(nodo):
        contador[0] += 1
        id_actual = f"n{contador[0]}"
        etiqueta = ETIQUETAS.get(nodo.valor, nodo.valor)
        dot.node(id_actual, etiqueta)

        if nodo.izquierdo is not None:
            id_izq = agregar(nodo.izquierdo)
            dot.edge(id_actual, id_izq)
        if nodo.derecho is not None:
            id_der = agregar(nodo.derecho)
            dot.edge(id_actual, id_der)

        return id_actual

    agregar(raiz)
    dot.render(ruta_salida, format="png", cleanup=True)
    return ruta_salida + ".png"


def procesar_expresion(expr, carpeta_salida=None, nombre_base=None):
    print(f"Expresion original : {expr}")

    try:
        tokens = tokenizar(expr)
    except ValueError as e:
        print(f"  ERROR de tokenizacion: {e}")
        print()
        return

    valida, error = validar_expresion(tokens)
    if not valida:
        print(f"  ERROR de validacion: {error}")
        print()
        return

    tokens_expandidos, pasos_expansion = expandir_extensiones(tokens)
    print("  Expansion de extensiones ('+', '?'):")
    for paso in pasos_expansion:
        print(f"    {paso}")

    tokens_formateados = insertar_concatenacion(tokens_expandidos)
    print(f"  Con concatenacion explicita: {''.join(tokens_formateados)}")

    postfix, pasos_conversion = infix_a_postfix(tokens_formateados)
    print("  Pasos de la conversion Shunting Yard:")
    for paso in pasos_conversion:
        print(f"    {paso}")

    print(f"  >> Expresion en POSTFIX: {''.join(postfix)}")

    try:
        raiz = construir_arbol(postfix)
    except ValueError as e:
        print(f"  ERROR al construir el arbol: {e}")
        print()
        return

    if carpeta_salida is not None:
        os.makedirs(carpeta_salida, exist_ok=True)
        ruta_base = os.path.join(carpeta_salida, nombre_base)
        ruta_png = dibujar_arbol(raiz, ruta_base)
        print(f"  >> Arbol sintactico guardado en: {ruta_png}")

    print()
    return raiz


def procesar_archivo(ruta, carpeta_salida="arboles"):
    if not os.path.exists(ruta):
        print(f"No se encontro el archivo: {ruta}")
        return
 
    with open(ruta, "r", encoding="utf-8") as f:
        lineas = [l.rstrip("\n") for l in f]
 
    for num, linea in enumerate(lineas, start=1):
        expr = linea.strip()
        if expr == "":
            continue
        print("=" * 70)
        print(f"Línea {num}: {expr}")
        print("-" * 70)
        procesar_expresion(expr, carpeta_salida=carpeta_salida, nombre_base=f"arbol_linea_{num}")


procesar_archivo("expresiones.txt")