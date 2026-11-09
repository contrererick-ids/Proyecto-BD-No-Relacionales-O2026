"""
populate.py: Plan para poblar las tres bases de datos.

Por ahora este archivo solo contiene comentarios que describen, paso a paso,
como se generaran y cargaran los datos de prueba. La logica se implementara
despues.

Las consultas que deben quedar cubiertas son las del menu de main.py:
    Cassandra: C1 a C8      MongoDB: M1 a M8      Dgraph: D1 a D8
"""

# =============================================================================
# PASO 0. Preparacion
# =============================================================================
# 1. Levantar los contenedores y verificar las conexiones:
#        python connect.py --up
# 2. Importar desde connect.py las funciones get_mongo_db(), get_cassandra_session()
#    y get_dgraph_client() para reutilizar las mismas conexiones.
#    Cada una regresa una tupla: (client, db), (cluster, session) y (stub, client);
#    al final se cierran con client.close(), cluster.shutdown() y stub.close().
# 3. Fijar una semilla (random.seed y Faker.seed) para que los datos generados
#    sean siempre los mismos y las consultas den resultados reproducibles.
# 4. Tomar la fecha de ejecucion como referencia ("hoy") para generar fechas
#    relativas (busquedas de los ultimos 6 meses, estancias pasadas, etc.).


# =============================================================================
# PASO 1. Generar los catalogos base
# =============================================================================
# Todos los datos se generan primero en Python y se guardan en data/ como JSON,
# para que los IDs sean los mismos en MongoDB, Cassandra y Dgraph.
# Los IDs son texto con prefijo (C01, D01, H001, U001, B0001...), por eso en
# Cassandra se guardan como TEXT.
#
# 1.1 Ciudades (data/cities.json)
#     - Lista fija de ~30 ciudades reales con aeropuerto (Guadalajara, CDMX,
#       Cancun, Madrid, Nueva York, etc.), cada una con city_id, city_name y country.
#
# 1.2 Categorias (data/categories.json)
#     - Lista fija: playa, cultura, aventura, gastronomia, naturaleza,
#       vida nocturna, compras, historia.
#
# 1.3 Destinos (data/destinations.json)
#     - ~40 destinos turisticos, cada uno con destination_id, destination_name,
#       country, 2 a 4 categorias y la ciudad con aeropuerto que le da servicio
#       (served_by). Ejemplo: Tulum -> Cancun.
#
# 1.4 Aerolineas (data/airlines.json)
#     - ~10 aerolineas con airline_id, airline_name y active (la mayoria True,
#       2 en False para probar el filtro de aerolineas activas).
#
# 1.5 Rutas aereas (data/routes.json)
#     - ~150 rutas directas entre pares de ciudades, con route_id, from_city,
#       to_city, airline_id y duration_minutes (calculada al azar segun la distancia
#       aproximada, entre 60 y 720 minutos).
#     - Se usan para D4 (vuelo directo desde tu ciudad), D6 (conectividad aerea)
#       y para generar los vuelos de MongoDB y las busquedas de Cassandra.
#
# 1.6 Hoteles (data/hotels.json)
#     - 3 a 6 hoteles por ciudad, con hotel_id, hotel_name (Faker), stars (1-5),
#       city_id, address, rating, average_nightly_rate, room_types (tipo, precio,
#       capacidad) e included_amenities (wifi, desayuno, alberca, gimnasio...).
#     - El rating de aqui es el mismo hotel_rating que se usa en C8.
#
# 1.7 Atracciones (data/attractions.json)
#     - 3 a 5 atracciones por destino, con attraction_id, attraction_name,
#       destination_id y una categoria.
#
# 1.8 Usuarios (data/users.json)
#     - ~200 usuarios con Faker: user_id, user_name, ciudad de residencia,
#       2 a 5 categorias de interes.
#     - Amistades: a cada usuario se le asignan 3 a 10 amigos al azar. La relacion
#       se guarda en ambos sentidos (si A es amigo de B, B es amigo de A).
#     - Visitas: cada usuario visito 2 a 8 destinos, con fecha de visita.
#     - Atracciones visitadas: algunas atracciones de los destinos que visito.
#
# 1.9 Reservaciones de hotel (data/bookings.json)
#     Se generan una sola vez y alimentan a las tres bases, para que una misma
#     reservacion tenga el mismo booking_id en MongoDB (M3), Cassandra (C3, C6,
#     C7, C8) y Dgraph (stayed_at).
#     - Cada usuario tiene 3 a 8 reservaciones: booking_id, user_id, hotel_id,
#       hotel_name, city, destination, room_type, number_of_guests,
#       number_of_rooms, booking_date, check_in_date, nights (1 a 10),
#       check_out_date y price (precio de la habitacion x noches x cuartos).
#     - ~15 % se marcan como canceladas, con cancellation_date (entre booking_date
#       y check_in_date), refund_amount (0 a 100 % del precio) y
#       cancellation_reason (cambio de planes, enfermedad, precio, clima...).
#     - Estancias: las reservaciones no canceladas con check_out_date anterior
#       a hoy. Son el historial de hoteles reservados (C8) y la base de las
#       reseñas y de la relacion stayed_at en Dgraph.
#
# 1.10 Reseñas de hotel (data/reviews.json)
#     - ~70 % de las estancias tienen reseña: user_id, hotel_id, hotel_name,
#       review_date (1 a 15 dias despues del check_out_date), rating (1 a 5)
#       y review_text (Faker, con un tono acorde al rating).
#     - El rating de la reseña es el mismo que se usa como facet en stayed_at,
#       para que D7 (hoteles recomendados por amigos) coincida con C4 y C5.


# =============================================================================
# PASO 2. Poblar MongoDB
# =============================================================================
# 2.1 Conectarse con get_mongo_db() y borrar las colecciones si ya existen
#     (drop) para empezar desde cero en cada ejecucion.
#
# 2.2 Coleccion hotels (M4)
#     - Insertar con insert_many() los hoteles de data/hotels.json con todos sus
#       campos anidados: hotel_id, hotel_name, stars, rating, city, address,
#       average_nightly_rate, room_types [{type, price, capacity}] e
#       included_amenities [...].
#
# 2.3 Coleccion flights (M2)
#     - Generar ~500 vuelos a partir de las rutas: flight_id, origin, destination,
#       airline, passenger_name (Faker), seat_preference (ventana/pasillo/en medio),
#       travel_class (turista/ejecutiva/primera), price, departure_date,
#       departure_time, flight_duration, arrival_date y arrival_hour (calculadas
#       con la duracion).
#
# 2.4 Coleccion hotel_bookings (M3)
#     - Insertar todas las reservaciones de data/bookings.json: booking_id,
#       user_id, hotel_id, booking_guest (nombre del usuario), number_of_guests,
#       number_of_rooms, room_types [...], check_in_date, check_out_date, price
#       y status (confirmada / cancelada).
#
# 2.5 Coleccion itineraries (M1, M5, M6, M7, M8)
#     - Generar ~100 itinerarios: itinerary_id, tour_name, start_date, end_date,
#       price, destinations [...] (2 a 5 destinos), planned_flights [...] (vuelos
#       con su duracion y precio) y hotel_stays [...] (hotel, noches y costo por
#       hotel).
#     - Con estos campos se calculan en agregaciones los dias, noches y horas de
#       vuelo (M6) y los costos totales de vuelos y hoteles de varios
#       itinerarios (M7).
#
# 2.6 Crear indices
#     - itineraries: price (M5, rango de precios) y destinations (M8, itinerarios
#       que incluyan una ciudad).
#     - hotels: hotel_id, hotel_name y city.
#     - flights: flight_id.   hotel_bookings: booking_id y user_id.


# =============================================================================
# PASO 3. Poblar Cassandra
# =============================================================================
# 3.1 Conectarse con get_cassandra_session(); el keyspace travel_platform se crea
#     automaticamente si no existe.
#
# 3.2 Crear las tablas con CREATE TABLE IF NOT EXISTS, leyendo las definiciones
#     de Cassandra/ (una tabla por consulta, como pide el modelo de Cassandra).
#     Todas ordenan sus filas con columnas de clustering, asi que ninguna consulta
#     necesita ORDER BY ni ALLOW FILTERING:
#     - C1 searches_by_user              PK user_id      | CK search_date DESC
#     - C2 flight_searches_by_user_dest  PK (user_id, destination) | CK search_date DESC
#     - C3 cancellations_by_user         PK user_id      | CK cancellation_date DESC, booking_id
#     - C4 reviews_by_user               PK user_id      | CK review_date DESC
#     - C5 reviews_by_hotel              PK hotel_id     | CK review_date DESC
#     - C6 bookings_by_user_price        PK user_id      | CK price DESC, booking_id
#     - C7 bookings_by_hotel_price       PK hotel_id     | CK price DESC, booking_id
#     - C8 hotel_stays_by_user           PK user_id      | CK hotel_rating DESC, stay_date DESC, booking_id
#     Las fechas que son CK y deben ser unicas (search_date, review_date) son
#     TIMEUUID; se generan con uuid_from_time() a partir de la fecha aleatoria.
#
# 3.3 Generar las busquedas de cada usuario de data/users.json:
#     - 20 a 60 busquedas en los ultimos 6 meses, con timestamps aleatorios:
#       origin (casi siempre su ciudad), destination, search_details (texto con
#       fechas, pasajeros y clase), departure_date y passengers.
#     - ~60 % son busquedas de vuelo (las demas son de hotel).
#
# 3.4 Insertar cada dato en todas las tablas que lo necesitan (desnormalizacion):
#     - Busqueda          -> searches_by_user y, si es de vuelo,
#                            flight_searches_by_user_dest.
#     - Reservacion       -> bookings_by_user_price y bookings_by_hotel_price
#                            (todas las de data/bookings.json).
#     - Cancelacion       -> cancellations_by_user (las canceladas).
#     - Estancia          -> hotel_stays_by_user (con hotel_rating de
#                            data/hotels.json, stay_date = check_in_date,
#                            nights y room_type).
#     - Reseña            -> reviews_by_user y reviews_by_hotel (data/reviews.json),
#                            con el mismo review_date en ambas tablas.
#     Se usaran sentencias preparadas (session.prepare) y
#     execute_concurrent_with_args para insertar rapido grandes volumenes.


# =============================================================================
# PASO 4. Poblar Dgraph
# =============================================================================
# 4.1 Conectarse con get_dgraph_client() y borrar los datos previos (drop_all).
#
# 4.2 Cargar el esquema de Dgraph/schema.dql con client.alter(), que define los
#     tipos (User, City, Destination, Category, Airline, Route, Hotel, Attraction),
#     los predicados y sus indices.
#
# 4.3 Insertar los nodos sin relaciones, en este orden: Category, City, Airline,
#     Destination, Hotel, Attraction, User. Cada nodo usa un blank node
#     (_:city_C01) para poder referenciarlo despues, y se guarda el uid que
#     regresa Dgraph en un diccionario {id_del_proyecto: uid}.
#
# 4.4 Insertar las relaciones usando ese diccionario:
#     - Destination: categories y served_by.
#     - Route: from_city, to_city y operated_by (un nodo Route por cada ruta).
#     - Hotel: hotel_city.   Attraction: attraction_destination y attraction_category.
#     - User: lives_in, interested_in, friends (en ambos sentidos),
#       visited (facet visit_date), stayed_at (facets rating y stay_date, tomados
#       de las estancias y reseñas de data/bookings.json y data/reviews.json;
#       si una estancia no tiene reseña, solo lleva stay_date)
#       y visited_attraction (facet visit_date).
#
# 4.5 Hacer commit de cada mutacion en lotes (por ejemplo, de 500 en 500)
#     para no generar transacciones demasiado grandes.


# =============================================================================
# PASO 5. Verificacion
# =============================================================================
# 5.1 Imprimir cuantos registros quedaron en cada base:
#     - MongoDB: count_documents() de cada coleccion.
#     - Cassandra: SELECT COUNT(*) por tabla (solo como verificacion, con pocos datos).
#     - Dgraph: count(uid) por cada tipo de nodo.
# 5.2 Revisar la consistencia entre bases: el numero de reseñas debe ser igual en
#     reviews_by_user y reviews_by_hotel, y las reservaciones de Cassandra deben
#     coincidir con los documentos de hotel_bookings en MongoDB.
# 5.3 Ejecutar una consulta de prueba en cada base para confirmar que los datos
#     se cargaron bien antes de correr main.py.