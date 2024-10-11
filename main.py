from flask import Flask, request, jsonify
import sqlite3
from sqlite3 import Error
from flasgger import Swagger

path = "products.db"
app = Flask(__name__)
swagger = Swagger(app)

shop = []
categorie = [{}]

try:
    con = sqlite3.connect(path)

    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS categorie(  
                id INTEGER PRIMARY KEY AUTOINCREMENT, categorie TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS all_products  
                (product TEXT, price INTEGER, categorie_id INTEGER,   
                FOREIGN KEY(categorie_id) REFERENCES categorie(id)) """)

    con.commit()
except Error:
    print(Error)
finally:
    con.close()


@app.route('/category/get_all', methods=['GET'])
def get_product():
    """  
    Get all categories  
    ---  
    responses:  
      200:  
        description: A list of categories  
        schema:  
          type: array  
          items:  
            type: object  
            properties:  
              id:  
                type: integer  
              categorie:  
                type: string  
    """
    try:
        con = sqlite3.connect(path)

        cur = con.cursor()
        cur.execute("""SELECT id,categorie FROM categorie """)
        categories = cur.fetchall()
        categories_list = [{"id": category[0], "categorie": category[1]}
                           for category in categories]

        return jsonify(categories_list)
    except Error:
        print(Error)


@app.route('/category/create', methods=["POST"])
def create_categorie():
    """  
    Create a new category  
    ---  
    parameters:  
      - name: categorie  
        in: body  
        required: true  
        schema:  
          type: object  
          properties:  
            categorie:  
              type: string  
    responses:  
      201:  
        description: The created category  
        schema:  
          type: object  
          properties:  
            id:  
              type: integer  
            categorie:  
              type: string  
    """
    new_categorie = {
        "categorie": request.json['categorie']
    }
    categorie.append(new_categorie)
    try:
        con = sqlite3.connect(path)

        cur = con.cursor()
        cur.execute("""INSERT INTO categorie(categorie)  
                    VALUES(?)""", (new_categorie['categorie'],))
        con.commit()
    except Error:
        print(Error)
    finally:
        con.close()
        return jsonify(new_categorie), 201


@app.route('/product/add', methods=['POST'])
def create_product():
    """  
    Create a new product  
    ---  
    parameters:  
      - name: product  
        in: body  
        required: true  
        schema:  
          type: object  
          properties:  
            product:  
              type: string  
            categorie:  
              type: string  
            price:  
              type: integer  
    responses:  
      201:  
        description: Product created successfully  
    """
    new_product = {
        "product": request.json['product'],
        "categorie": request.json["categorie"],
        "price": request.json['price']
    }
    shop.append(new_product)
    con = sqlite3.connect(path)

    cur = con.cursor()
    cur.execute("""SELECT id FROM categorie WHERE categorie=? """,
                (new_product['categorie'],))
    category = cur.fetchone()

    if category is None:
        return jsonify({"message": "Category not found"}), 404

    category_id = category[0]
    cur.execute("""INSERT INTO all_products(product, price, categorie_id)  
                   VALUES(?, ?, ?)""", (new_product['product'], new_product['price'], category_id))

    con.commit()
    con.close()
    return jsonify({"message": "Product created successfully"}), 201


@app.route('/get/product/<string:category>', methods=['GET'])
def get_product_by_categorie(category):
    """  
    Get products by category  
    ---  
    parameters:  
      - name: category  
        in: path  
        type: string  
        required: true  
    responses:  
      200:  
        description: A list of products in the specified category  
        schema:  
          type: array  
          items:  
            type: object  
            properties:  
              product:  
                type: string  
              price:  
                type: integer  
      404:  
        description: Category not found  
    """
    con = sqlite3.connect(path)

    cur = con.cursor()
    cur.execute("""SELECT product,price FROM all_products  
                WHERE categorie_id = (SELECT id FROM categorie WHERE categorie = ?) """, (category,))
    products = cur.fetchall()
    product_list = [{"product": product[0], "price": product[1]}
                    for product in products]
    con.close()
    return jsonify(product_list)


@app.route('/update/product', methods=['PUT'])
def update_product():
    """  
    Update an existing product  
    ---  
    parameters:  
      - name: product  
        in: body  
        required: true  
        schema:  
          type: object  
          properties:  
            product:  
              type: string  
            categorie:  
              type: string  
            price:  
              type: integer  
    responses:  
      200:  
        description: Product updated successfully  
      404:  
        description: Product not found  
    """
    product_name = request.json['product']
    product_to_update = next(
        (product for product in shop if product['product'] == product_name), None)

    if product_to_update:
        product_to_update['categorie'] = request.json.get(
            'categorie', product_to_update['categorie'])
        product_to_update['price'] = request.json.get(
            'price', product_to_update['price'])
        return jsonify({"message": "Product updated", "product": product_to_update}), 200
    else:
        return jsonify({"message": "Product not found"}), 404


@app.route('/product/delete', method=['DELETE'])
def product_delete():
    """  
  Delete an existing product  
  ---  
  parameters:  
    - name: product  
      in: body  
      required: true  
      schema:  
        type: object  
        properties:  
          product:  
            type: string  

  responses:  
    200:  
      description: Product deleted successfully  
    404:  
      description: Product not found  
  """
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()

        product_name = request.json['product']
        cur.execute("""SELECT id FROM  all_products WHERE  product=?
                    """, product_name,)
        product = cur.fetchone()

        if product is None:
            return jsonify({"message": "product not found "}), 404
        cur.execute(
            """DELETE FROM  all_products WHERE product=? """, (product_name))
        con.commit()
        return jsonify({"message": "product deleted succesfully"}), 200
    except Error as e:
        print(e)
        return jsonify({"message ": " somthing went wrong "})
    finally:
        con.close()


if __name__ == "__main__":
    app.run()
