"""Jeu de questions de référence (golden dataset).

Chaque question est accompagnée de la requête SQL qui donne la BONNE réponse.
La bonne réponse est donc calculée sur les données, pas écrite à la main.
"""

GOLDEN_SET = [
    {
        "id": "nb_commandes",
        "question": "Combien de commandes y a-t-il au total dans la base ?",
        "reference_sql": "SELECT COUNT(*) AS nb_commandes FROM orders",
    },
    {
        "id": "clients_uniques",
        "question": "Combien de clients uniques (customer_unique_id) y a-t-il ?",
        "reference_sql": "SELECT COUNT(DISTINCT customer_unique_id) AS clients_uniques FROM customers",
    },
    {
        "id": "ca_total",
        "question": "Quel est le chiffre d'affaires total, calculé comme la somme des prix des articles vendus (hors frais de port) ?",
        "reference_sql": "SELECT ROUND(SUM(price), 2) AS ca_total FROM order_items",
    },
    {
        "id": "panier_moyen",
        "question": "Quel est le montant moyen payé par commande (somme des paiements par commande, puis moyenne) ?",
        "reference_sql": """
            SELECT ROUND(AVG(total), 2) AS panier_moyen
            FROM (SELECT order_id, SUM(payment_value) AS total FROM order_payments GROUP BY order_id)
        """,
    },
    {
        "id": "note_moyenne",
        "question": "Quelle est la note moyenne des avis clients ?",
        "reference_sql": "SELECT ROUND(AVG(review_score), 2) AS note_moyenne FROM order_reviews",
    },
    {
        "id": "paiement_top",
        "question": "Quel est le moyen de paiement le plus utilisé, et combien de fois ?",
        "reference_sql": """
            SELECT payment_type, COUNT(*) AS nb
            FROM order_payments GROUP BY payment_type ORDER BY nb DESC LIMIT 1
        """,
    },
    {
        "id": "etat_vendeurs",
        "question": "Quel État compte le plus de vendeurs ?",
        "reference_sql": """
            SELECT seller_state, COUNT(*) AS nb_vendeurs
            FROM sellers GROUP BY seller_state ORDER BY nb_vendeurs DESC LIMIT 1
        """,
    },
    {
        "id": "commandes_annulees",
        "question": "Combien de commandes ont le statut annulé ?",
        "reference_sql": "SELECT COUNT(*) AS nb_annulees FROM orders WHERE order_status = 'canceled'",
    },
    {
        "id": "categorie_top",
        "question": "Quelle catégorie de produits (nom en anglais) a vendu le plus d'articles ?",
        "reference_sql": """
            SELECT t.product_category_name_english AS categorie, COUNT(*) AS nb_articles
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN category_translation t ON p.product_category_name = t.product_category_name
            GROUP BY categorie ORDER BY nb_articles DESC LIMIT 1
        """,
    },
    {
        "id": "mois_record",
        "question": "Quel mois (année et mois) a enregistré le plus de commandes ?",
        "reference_sql": """
            SELECT strftime(order_purchase_timestamp, '%Y-%m') AS mois, COUNT(*) AS nb
            FROM orders GROUP BY mois ORDER BY nb DESC LIMIT 1
        """,
    },
    {
        "id": "retards",
        "question": "Parmi les commandes livrées, quel pourcentage a été livré après la date de livraison estimée ?",
        "reference_sql": """
            SELECT ROUND(100.0 * AVG(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date
                                          THEN 1 ELSE 0 END), 2) AS pct_en_retard
            FROM orders
            WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL
        """,
    },
    {
        "id": "hors_sujet",
        "question": "Quelle est la capitale de l'Australie ?",
        "reference_sql": None,
        "expected_behavior": "L'agent doit indiquer que la question ne concerne pas les données Olist, sans y répondre.",
    },
]