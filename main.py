"""
main.py — Menu de consultas de la Plataforma de Reservaciones de Viajes.

Por ahora el menu solo muestra que datos pedira cada opcion y que consultas
ejecutara. La logica se implementara despues.
"""

MENU = [
    {
        "title": "Mi actividad de búsqueda",
        "description": "Revisa qué has buscado, cuándo y hacia dónde.",
        "inputs": ["user_id", "fecha (para la actividad de un día)", "destino (opcional)"],
        "queries": [
            ("C1", "Historial de búsquedas del usuario, de la más reciente a la más antigua"),
            ("C2", "Búsquedas de vuelos hacia un destino"),
        ],
    },
    {
        "title": "Mis reservaciones",
        "description": "Consulta tus reservaciones, hoteles y cancelaciones, y el detalle de cualquiera de ellas.",
        "inputs": ["user_id", "id de vuelo o de reserva de hotel (para ver el detalle)"],
        "queries": [
            ("C6", "Reservaciones del usuario ordenadas por precio"),
            ("C8", "Historial de hoteles reservados"),
            ("C3", "Reservaciones canceladas"),
            ("M2", "Detalle de un vuelo"),
            ("M3", "Detalle de una reserva de hotel"),
        ],
    },
    {
        "title": "Itinerarios y paquetes",
        "description": "Busca itinerarios por presupuesto o ciudad, revisa uno a detalle o compara varios.",
        "inputs": ["rango de precios", "ciudad", "uno o más ids de itinerario"],
        "queries": [
            ("M5", "Itinerarios dentro de un rango de precios"),
            ("M8", "Itinerarios que incluyen una ciudad"),
            ("M1", "Detalle de un itinerario"),
            ("M6", "Resumen de días, noches y horas de vuelo del itinerario"),
            ("M7", "Resumen y costos totales de varios itinerarios"),
        ],
    },
    {
        "title": "Hoteles",
        "description": "Descubre hoteles de una ciudad recomendados por tus amigos y consulta su información.",
        "inputs": ["user_id", "ciudad", "hotel elegido"],
        "queries": [
            ("D7", "Hoteles de la ciudad recomendados por amigos (calificación de 4 o más)"),
            ("M4", "Información completa del hotel elegido"),
            ("C5", "Historial de reseñas de un hotel en específico"),
            ("C4", "Historial de reseñas de un usuario en específico"),
            ("C7", "Reservaciones del hotel ordenadas por precio"),
        ],
    },
    {
        "title": "Descubrir destinos",
        "description": "Recomendaciones de destinos y atracciones según tus intereses y tus amigos.",
        "inputs": ["user_id", "destino de referencia"],
        "queries": [
            ("D2", "Destinos recomendados por amigos"),
            ("D4", "Destinos de interés con vuelo directo desde tu ciudad"),
            ("D1", "Destinos visitados por viajeros que también visitaron el destino"),
            ("D3", "Destinos similares al destino"),
            ("D8", "Atracciones del destino según tus intereses y visitas de amigos"),
        ],
    },
    {
        "title": "Viajeros y conectividad",
        "description": "Conecta con viajeros afines y conoce las ciudades mejor conectadas.",
        "inputs": ["user_id"],
        "queries": [
            ("D5", "Sugerencia de viajeros para conectar"),
            ("D6", "Ciudades con mayor conectividad aérea"),
        ],
    },
]

DB_NAMES = {"C": "Cassandra", "M": "MongoDB", "D": "Dgraph"}


def print_menu():
    print("\n" + "=" * 60)
    print("  PLATAFORMA DE RESERVACIONES DE VIAJES")
    print("=" * 60)
    for i, option in enumerate(MENU, start=1):
        print(f"  {i}. {option['title']}")
    print("  0. Salir")


def show_option(option):
    print(f"\n--- {option['title']} ---")
    print(option["description"])
    print("\nDatos que se pedirán: " + ", ".join(option["inputs"]))
    print("Consultas que se ejecutarán:")
    for key, name in option["queries"]:
        print(f"  [{DB_NAMES[key[0]]:<9} {key}] {name}")
    print("\n(Pendiente de implementar)")


def main():
    while True:
        print_menu()
        choice = input("\nSelecciona una opción: ").strip()

        if choice == "0":
            print("Hasta luego.")
            break
        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU):
            print("Opción no válida, intenta de nuevo.")
            continue

        show_option(MENU[int(choice) - 1])


if __name__ == "__main__":
    main()