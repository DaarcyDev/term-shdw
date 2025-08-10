import argparse

def get_config():
    parser = argparse.ArgumentParser(description="Term-Shdw: efecto cometa interactivo en terminal.")

    parser.add_argument("--color-head", default="681414", help="Color HEX de la cabeza del cometa (sin #).")
    parser.add_argument("--color-tail", default="7b87ed", help="Color HEX de la cola del cometa (sin #).")
    parser.add_argument("--symbol-head", default="{#@#}", help="Símbolo para la cabeza del cometa.")
    parser.add_argument("--trail-length", type=int, default=20, help="Longitud máxima de la estela.")
    parser.add_argument("--frame-delay", type=float, default=0.0001, help="Retraso entre frames.")

    return parser.parse_args()
