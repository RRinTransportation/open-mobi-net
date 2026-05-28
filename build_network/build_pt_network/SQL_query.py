sql_links_query = """
                SELECT
                    t.trip_id,
                    r.route_id,
                    r.shortname AS line_name,
                    r.route_type AS mode,
                    ST_AsText(r.geometry) AS geometry
                FROM
                    trips AS t
                JOIN
                    routes AS r ON t.pattern_id = r.pattern_id
                WHERE
                    r.geometry IS NOT NULL;
                """

sql_enriched_nodes_query = """
            WITH StopPatterns AS (
                -- Étape 1: Créer une liste unique de chaque arrêt (stop_id) 
                -- et de chaque ligne (pattern_id) qui le dessert.
                SELECT from_stop AS stop_id, pattern_id FROM route_links
                UNION
                SELECT to_stop AS stop_id, pattern_id FROM route_links
            )
            -- Étape 2: Joindre cette liste avec les tables 'stops' et 'routes'
            SELECT
                s.stop_id,
                s.name AS stop_name,
                ST_AsText(s.geometry) AS geometry,
                -- Étape 3: Agréger les informations pour chaque arrêt
                GROUP_CONCAT(DISTINCT r.shortname) AS lines,
                GROUP_CONCAT(DISTINCT r.route_type) AS modes,
                GROUP_CONCAT(DISTINCT r.route_id) AS route_ids
            FROM
                stops AS s
            JOIN
                StopPatterns AS sp ON s.stop_id = sp.stop_id
            JOIN
                routes AS r ON sp.pattern_id = r.pattern_id
            GROUP BY
                s.stop_id, s.name, s.geometry;
            """