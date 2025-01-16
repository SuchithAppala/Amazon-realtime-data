from flask import Flask,request,render_template,redirect,session
import pymysql
import os
import pandas as pd
import pickle
from Mail import send_email
import requests
import pandas as pd
from nltk.tokenize import word_tokenize
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
import sklearn

analyzer = SentimentIntensityAnalyzer()
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = APP_ROOT+"/static/products/csv"

conn=pymysql.connect(host="localhost", user="root",password="Chintu123", db="Amazon_realtime_data")
cursor = conn.cursor()
app =Flask(__name__)
admin_username = 'admin'
admin_password = 'admin'
app.secret_key ="admin"

live_data_key = "6f3aa5f6a0msh30c3da59b6da93cp1aa8cbjsne72742bc9937"

with open('rf.pkl', 'rb') as model_file:
    loaded_model = pickle.load(model_file)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login_action",methods=['post'])
def admin_login_action():
    username =request.form.get("username")
    password = request.form.get("password")
    if username == admin_username and password == admin_password:
        session['role'] ='admin'
        return redirect("/admin_home")
    else:
        return render_template("message.html",message="Invalid Login Details")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/seller_registration")
def seller_registration():
    return render_template("seller_registration.html")


@app.route("/seller_registration_action",methods=['post'])
def seller_registration_action():
      name = request.form.get("name")
      email = request.form.get("email")
      phone = request.form.get("phone")
      password = request.form.get("password")
      address = request.form.get("address")
      count =cursor.execute("select * from sellers where email='"+str(email)+"'")
      if count >0:
          return render_template("message.html",message="This Mail Is Already Exist")
      count =cursor.execute("select * from sellers where phone='"+str(phone)+"'")
      if count >0:
          return render_template("message.html",message="This Phone Number Is Already Exist")
      cursor.execute("insert into sellers(name,email,phone,password,address,status)values('"+str(name)+"','"+str(email)+"','"+str(phone)+"','"+str(password)+"','"+str(address)+"','Not Verified')")
      conn.commit()
      return render_template("message.html",message="Seller Registered Successfully")


@app.route("/seller_login")
def seller_login():
    return render_template("seller_login.html")


@app.route("/seller_login_action", methods=["post"])
def seller_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    count = cursor.execute("select * from sellers where email='"+str(email)+"' and password='"+str(password)+"'")
    if count > 0:
          seller = cursor.fetchall()
          if seller[0][6] =='Verified':
              session['seller_id'] = seller[0][0]
              session['role'] = 'sellers'
              return redirect("/seller_home")
          else:
              return render_template("message.html", message="Your Account Not Verified")
    else:
        return render_template("message.html", message="Invalid login details")


@app.route("/seller_home")
def seller_home():
    return render_template("seller_home.html")


@app.route("/view_seller")
def view_seller():
    cursor.execute("select * from sellers")
    sellers = cursor.fetchall()
    return render_template("view_seller.html", sellers=sellers)


@app.route("/authorize")
def authorize():
    seller_id = request.args.get("seller_id")
    cursor.execute("update sellers set status='Verified' where seller_id='"+str(seller_id)+"'")
    conn.commit()
    return redirect("/view_seller")


@app.route("/un_authorize")
def un_authorize():
    seller_id = request.args.get("seller_id")
    cursor.execute("update sellers set status='Not Verified' where seller_id='"+str(seller_id)+"'")
    conn.commit()
    return redirect("/view_seller")


@app.route("/customer_registration")
def customer_registration():
    return render_template("customer_registration.html")


@app.route("/customer_registration_action",methods=['post'])
def customer_registration_action():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    address = request.form.get("address")
    count = cursor.execute("select * from customers where email='" + str(email) + "'")
    if count > 0:
        return render_template("message.html", message="Duplicate email address")
    count = cursor.execute("select * from customers where phone='" + str(phone) + "'")
    if count > 0:
        return render_template("message.html", message="Duplicate Phone")
    cursor.execute("insert into customers(name,email,phone,password,address)values('"+str(name)+"','"+str(email)+"','"+str(phone)+"','"+str(password)+"','"+str(address)+"' )")
    conn.commit()
    return render_template("message.html", message="Customer Registered Successfully")


@app.route("/customer_login")
def customer_login():
    return render_template("customer_login.html")


@app.route("/customer_login_action", methods=["post"])
def customer_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    count = cursor.execute("select * from customers where email='"+str(email)+"' and password='"+str(password)+"'")
    customers = cursor.fetchall()
    if count > 0:
        session['customer_id'] = customers[0][0]
        session['role'] = 'customers'
        return redirect("/customer_home")
    else:
        return render_template("message.html", message="Invalid login details")

@app.route("/customer_home")
def customer_home():
    return render_template("customer_home.html")

@app.route("/add_products")
def add_products():
    return render_template("add_products.html")

@app.route("/add_product_action", methods=['post'])
def add_product_action():
    file = request.files.get("file")
    print("hll")
    category_name = request.form.get("category_name")
    seller_id = session['seller_id']
    path = CSV_PATH + "/" + file.filename
    file.save(path)
    data = pd.read_csv(path)
    total =1

    for i in range(data.shape[0]):
        if len(data.iloc[i].values) == 25:
            total = total + 1
            count = cursor.execute("select * from products where asin='"+str(data.iloc[i].values[2])+"' ")
            if count == 0:
                query = "insert into products(asin,rankk,product_title,product_price,product_photo,category, original_price)values('" + str(data.iloc[i].values[2]).replace("'", "").replace("’", "") + "', '"+str(data.iloc[i].values[1])+"', '" + str(data.iloc[i].values[3]).replace("'", "").replace("’", "") + "', '" + str(data.iloc[i].values[4]).replace("$", "") + "', '" + str(data.iloc[i].values[8]) + "','"+str(category_name)+"', '" + str(data.iloc[i].values[4]).replace("$", "") + "')"
                cursor.execute(query)
                conn.commit()
                product_id = cursor.lastrowid
            else:
                products = cursor.fetchall()
                product_id = products[0][0]
            print(data.iloc[i].values[0])
            print(data.iloc[i].values[1])
            print(data.iloc[i].values[2])

            query = "insert into ratings(review_comment,review_title,review_star_ratings,review_date,number_people_helpfull,sentiment,sentiment_score,product_id)values('" + str(data.iloc[i].values[13]).replace("'","").replace("’","")+ "', '" + str(data.iloc[i].values[12]).replace("'","").replace("’", "") + "', '" + str(data.iloc[i].values[14]) + "', '" + str(data.iloc[i].values[19]) + "', '" + str(data.iloc[i].values[20]) + "', '" + str(data.iloc[i].values[21]) + "', '" + str(data.iloc[i].values[23]) + "','"+str(product_id)+"')"
            # print(query)
            print(query)
            cursor.execute(query)
            conn.commit()
            rating_id = cursor.lastrowid
            tags = data.iloc[i].values[22].replace("[","").replace("'","").replace("]","").split(",")
            for tag in tags:
                cursor.execute("insert into tags(tag,rating_id)values('" + str(tag) + "','"+str(rating_id)+"')")
                conn.commit()
    print(total)
    return render_template("smessage.html", message="Products Added Successfully")



@app.route("/view_products")
def view_products():
    category = request.args.get("category_name", "")
    product_title = request.args.get("product_title", "")
    data_type = request.args.get("data_type", "csv")

    if category and product_title:
        query = f"SELECT * FROM products WHERE product_title LIKE '%{product_title}%' AND category='{category}' AND data_type='{data_type}' ORDER BY rankk ASC"
    elif category:
        query = f"SELECT * FROM products WHERE category='{category}' AND data_type='{data_type}' ORDER BY rankk ASC"
    elif product_title:
        query = f"SELECT * FROM products WHERE product_title LIKE '%{product_title}%' AND data_type='{data_type}' ORDER BY rankk ASC"
    else:
        query = f"SELECT * FROM products WHERE data_type='{data_type}' ORDER BY rankk ASC"

    cursor.execute(query)
    products = cursor.fetchall()

    products_with_sentiment = [(product, get_sentiment_score_by_product_id(product[0])) for product in products]
    sorted_products = sorted(products_with_sentiment, key=lambda x: x[1], reverse=True)
    products = [product[0] for product in sorted_products]

    return render_template("view_products.html",products=products,category_name=category,product_title=product_title,get_quantity_by_product_id=get_quantity_by_product_id,get_price_by_product_id=get_price_by_product_id,get_rating_by_product_id=get_rating_by_product_id,get_sentiment_score_by_product_id=get_sentiment_score_by_product_id,data_type=data_type)

@app.route("/view_products2")
def view_products2():
    query = "select * from products where data_type='live'"
    count = cursor.execute(query)
    if count > 0:
        return redirect("/view_products?data_type=live")
    nltk.download('punkt_tab')
    print('product details fetching...............')
    url = "https://real-time-amazon-data.p.rapidapi.com/best-sellers"
    querystring = {"category": "software", "type": "BEST_SELLERS", "page": "1", "country": "US"}
    headers = {
        "x-rapidapi-key": live_data_key,
        "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring)
    print(response.json())
    software_products = response.json()['data']['best_sellers']
    live_data = pd.DataFrame(software_products)
    print(live_data)
    live_asins = live_data['asin'].unique()
    asin_list = live_asins
    print('product reviews fetching.......................')
    url = "https://real-time-amazon-data.p.rapidapi.com/product-reviews"
    headers = {
        "x-rapidapi-key": live_data_key,
        "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
    }
    all_reviews_df = pd.DataFrame()
    product_count = 0
    for asin in asin_list:
        querystring = {
            "asin": asin,
            "country": "US",
            "sort_by": "TOP_REVIEWS",
            "star_rating": "ALL",
            "verified_purchases_only": "false",
            "images_or_videos_only": "false",
            "current_format_only": "false",
            "page": "1"
        }
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            reviews_data = response.json()
            asin_value = reviews_data.get("parameters", {}).get("asin")
            reviews = reviews_data.get("data", {}).get("reviews", [])
            reviews_df = pd.DataFrame(reviews)
            reviews_df["asin"] = asin_value
            all_reviews_df = pd.concat([all_reviews_df, reviews_df], ignore_index=True)
        else:
            print(f"Failed to fetch data for ASIN {asin}. Status code: {response.status_code}")
    print(all_reviews_df)
    print(all_reviews_df.info())
    print('merging data....................')
    merged_df = pd.merge(all_reviews_df, live_data, on='asin', how='inner')
    print('sentiment addition...................')
    merged_df[['sentiment', 'tags', 'sentiment_score']] = merged_df['review_comment'].apply(
        lambda x: pd.Series(extract_top_contributing_words_unique(x))
    )
    merged_df['category'] = 'software'
    print('dataframe columns-----------------------')
    print(merged_df.info())
    data = merged_df
    print('data columns--------------------')
    print(data.info())
    total = 1
    for i in range(data.shape[0]):
        print(len(data.iloc[i].values))

        print(data.iloc[i].values)
        if len(data.iloc[i].values) == 26:
            total = total + 1
            count = cursor.execute("select * from products where asin='" + str(data.iloc[i].values[13]) + "' and data_type='live' ")
            if count == 0:
                query = "insert into products(asin,rankk,product_title,product_price,product_photo,category, original_price,data_type)values('" + str(data.iloc[i].values[13]).replace("'", "").replace("’", "") + "', '" + str(data.iloc[i].values[14]) + "', '" + str(data.iloc[i].values[15]).replace("'", "").replace("’","") + "', '" + str(data.iloc[i].values[16]).replace("$", "") + "', '" + str(data.iloc[i].values[20]).replace(",", "") + "','" + str(data.iloc[i].values[25]) + "', '" + str(data.iloc[i].values[16]).replace("$", "") + "', 'live')"
                cursor.execute(query)
                conn.commit()
                product_id = cursor.lastrowid
            else:
                products = cursor.fetchall()
                product_id = products[0][0]
            print(data.iloc[i].values[0])
            print(data.iloc[i].values[1])
            print(data.iloc[i].values[2])

            query = "insert into ratings(review_comment,review_title,review_star_ratings,review_date,number_people_helpfull,sentiment,sentiment_score,product_id)values('" + str(
                data.iloc[i].values[2]).replace("'", "").replace("’", "") + "', '" + str(
                data.iloc[i].values[1]).replace("'", "").replace("’", "") + "', '" + str(
                data.iloc[i].values[3]) + "', '" + str(data.iloc[i].values[9]) + "', '" + str(
                data.iloc[i].values[11]) + "', '" + str(data.iloc[i].values[23]) + "', '" + str(
                data.iloc[i].values[22]) + "','" + str(product_id) + "')"
            print(query)
            print(query)
            cursor.execute(query)
            conn.commit()
            rating_id = cursor.lastrowid
            tags = data.iloc[i].values[24]
            print('.........tags--------------')
            print(tags)
            for tag in tags:
                cursor.execute("insert into tags(tag,rating_id)values('" + str(tag) + "','" + str(rating_id) + "')")
                conn.commit()
            sentiment_score = get_sentiment_score_by_product_id(product_id)
            cursor.execute("update products set sentiment_score='" + str(sentiment_score) + "' where product_id='" + str(product_id) + "'")
            conn.commit()
    print(total)
    return redirect("/view_products?data_type=live")


def extract_top_contributing_words_unique(review):
    sentiment_scores = analyzer.polarity_scores(review)
    compound = sentiment_scores['compound']
    if compound > 0.05:
        sentiment_label = "Positive"
    elif compound < -0.05:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"
    tokens = word_tokenize(review)
    word_scores = []
    for token in tokens:
        if not token.isalpha():
            continue
        token_score = analyzer.polarity_scores(token)['compound']
        if sentiment_label == "Positive" and token_score > 0.05:
            word_scores.append((token, token_score))
        elif sentiment_label == "Negative" and token_score < -0.05:
            word_scores.append((token, token_score))
    top_words = [word for word, score in sorted(word_scores, key=lambda x: abs(x[1]), reverse=True)]
    unique_top_words = list(dict.fromkeys(top_words))[:3]
    return compound, sentiment_label, unique_top_words

@app.route("/view_product")
def view_product():
    product_id = request.args.get("product_id")
    cursor.execute("select * from products where product_id='"+str(product_id)+"'")
    products = cursor.fetchall()
    cursor.execute("select * from ratings where product_id = '"+str(product_id)+"' ")
    ratings = cursor.fetchall()
    return render_template("view_product.html",product=products[0],ratings=ratings,get_tag_by_rating_id=get_tag_by_rating_id, get_rating_by_product_id=get_rating_by_product_id)


def get_tag_by_rating_id(rating_id):
    cursor.execute("select * from tags where rating_id='"+str(rating_id)+"'")
    tags = cursor.fetchall()
    if len(tags) == 0:
        return None
    return tags[0]

@app.route("/update_quantity")
def update():
    data_type = request.args.get("data_type")
    category_name = request.args.get("category_name")
    product_title = request.args.get("product_title")
    product_id = request.args.get("product_id")
    return render_template("update_quantity.html", product_id=product_id,product_title=product_title, category_name=category_name, data_type=data_type)




@app.route("/update_quantity_action")
def update_action():
    data_type = request.args.get("data_type")
    product_id = request.args.get("product_id")
    quantity = request.args.get("quantity")
    category_name = request.args.get("category_name")
    product_title = request.args.get("product_title")
    seller_id = session['seller_id']
    count = cursor.execute("select * from inventory where seller_id ='"+str(seller_id)+"' and product_id= '"+str(product_id)+"' ")
    if count == 0:
        if int(quantity)>0:
             cursor.execute("insert into inventory(quantity,seller_id,product_id)values('"+str(quantity)+"','"+str(seller_id)+"','"+str(product_id)+"')")
             conn.commit()
        else:
            return render_template("cmessage.html", message="Invalid Quantity")
    else:
        inventories = cursor.fetchall()
        inventory_id = inventories[0][0]
        quantity2 = inventories[0][1]

        if int(quantity2) + int(quantity) > 0:
            cursor.execute("update inventory set quantity=quantity+'"+str(quantity)+"'where product_id='"+str(product_id)+"' and seller_id='"+str(seller_id)+"' ")
            conn.commit()

            cursor.execute("select * from notification where inventory_id='" + str(inventory_id) + "' and status = 'Not Notified' ")
            notifications = cursor.fetchall()
            for notification in notifications:
                customer_id=notification[4]
                cursor.execute("select * from customers where customer_id='" + str(customer_id) + "' ")
                customer = cursor.fetchone()
                email = (customer[2])
                send_email(
                    "Your Required Product is Back in Stock - Order Now!",
                    "Dear Customer,\n\nWe are excited to inform you that the product you were looking for is now available!\n\nThank you for choosing us.",
                    email
                )
                cursor.execute("update notification set status = 'New Notification' where inventory_id = '" + str(inventory_id) + "' and status = 'Not Notified' ")
                conn.commit()
        else:
            return render_template("cmessage.html", message="Invalid Quantity")
    if data_type == "csv":
        return redirect("/view_products?category_name="+category_name+"&product_title="+product_title)
    else:
        return redirect("/view_products?data_type=live")


@app.route("/buy")
def buy():
    product_id = request.args.get("product_id")
    cursor.execute("select * from inventory where product_id='"+str(product_id)+"'")
    inventories = cursor.fetchall()
    return render_template("buy.html", inventories=inventories,product_id=product_id,get_product_by_product_id=get_product_by_product_id)

def get_product_by_product_id(product_id):
    cursor.execute("select * from products where product_id='"+str(product_id)+"'")
    product = cursor.fetchone()
    return product



@app.route("/add_cart")
def add_cart():
    inventory_id = request.args.get("inventory_id")
    quantity = request.args.get("quantity")
    customer_id = session['customer_id']
    quantity = int(quantity)
    cursor.execute("select * from inventory where inventory_id='" + str(inventory_id) + "'")
    inventories = cursor.fetchall()
    available_quantity = inventories[0][1]
    seller_id = inventories[0][2]

    if int(quantity) > int(available_quantity):
        purchasable_quantity = available_quantity
        excess_quantity = int(quantity) - int(available_quantity)
        cursor.execute("insert into notification(status, quantity, inventory_id, customer_id) values('Not Notified', '" + str(excess_quantity) + "', '" + str(inventory_id) + "', '" + str(customer_id) + "')")
        conn.commit()
    else:
        purchasable_quantity = quantity

    count = cursor.execute("select * from orders where customer_id='" + str(customer_id) + "' and seller_id='" + str(seller_id) + "' and status='Cart'")
    if count == 0:
        cursor.execute("insert into orders(status, seller_id, customer_id) values('Cart', '" + str(seller_id) + "', '" + str(customer_id) + "')")
        order_id = cursor.lastrowid
    else:
        orders = cursor.fetchall()
        order_id = orders[0][0]

    count = cursor.execute("select * from order_items where inventory_id='" + str(inventory_id) + "' and order_id='" + str(order_id) + "'")
    if count == 0:
        cursor.execute("insert into order_items(quantity, order_id, inventory_id) values('" + str(purchasable_quantity) + "', '" + str(order_id) + "', '" + str(inventory_id) + "')")
    else:
        cursor.execute("update order_items set quantity = quantity + '" + str(purchasable_quantity) + "' where order_id = '" + str(order_id) + "' and inventory_id = '" + str(inventory_id) + "'")
    conn.commit()

    if int(quantity) > int(available_quantity):
        return render_template("cmessage.html",message="Some products added to notification due to insufficient stock. Available quantity added to cart.")
    else:
        return render_template("cmessage.html", message="Products Added into Cart")


@app.route("/view_orders")
def view_orders():
    query = ""
    view_type = request.args.get("view_type")
    if session['role'] == 'customers':
        customer_id = session['customer_id']
        if view_type == "cart":
             query = "select * from orders where customer_id='"+str(customer_id)+"' and status='cart'"
        elif view_type == "ordered":
            query ="select * from orders where customer_id='"+str(customer_id)+"' and (status='Ordered' or status='Dispatched')"
        elif view_type == "history":
            query ="select * from orders where customer_id='"+str(customer_id)+"' and (status='Delivered' or status='Cancelled')"
    elif session['role'] == 'sellers':
        seller_id = session['seller_id']
        if view_type == "ordered":
             query = "select * from orders where seller_id='"+str(seller_id)+"' and status='ordered'"
        elif view_type == "dispatched":
            query ="select * from orders where seller_id='"+str(seller_id)+"' and status='dispatched'"
        elif view_type == "history":
            query ="select * from orders where seller_id='"+str(seller_id)+"' and (status='delivered' or status='cancelled')"
    cursor.execute(query)
    orders = cursor.fetchall()
    return render_template("view_orders.html",int=int, orders=orders,get_customer_by_customer_id=get_customer_by_customer_id,get_seller_by_seller_id=get_seller_by_seller_id,get_order_items_by_order_id=get_order_items_by_order_id,get_product_by_inventory_id=get_product_by_inventory_id)


def get_customer_by_customer_id(customer_id):
    cursor.execute("select * from customers where customer_id='"+str(customer_id)+"'")
    customer = cursor.fetchone()
    return customer

def get_seller_by_seller_id(seller_id):
    cursor.execute("select * from sellers where seller_id='"+str(seller_id)+"'")
    seller = cursor.fetchone()
    return seller


def get_order_items_by_order_id(order_id):
    cursor.execute("select * from order_items where order_id='"+str(order_id)+"'")
    order_items = cursor.fetchall()
    return order_items

def get_product_by_inventory_id(inventory_id):
    cursor.execute("select * from products where product_id in(select product_id from inventory where inventory_id='"+str(inventory_id)+"')")
    product = cursor.fetchone()
    return product


@app.route("/send_price_request")
def send_price_request():
    category_name = request.args.get("category_name")
    product_title = request.args.get("product_title")
    product_id = request.args.get("product_id")
    data_type = request.args.get("data_type")
    price = request.args.get("price")
    price = int(float(price))+ 1
    return render_template("send_price_request.html", product_id=product_id,category_name=category_name, product_title=product_title, price=price, float=float, data_type=data_type)

@app.route("/send_price_request_action")
def send_price_request_action():
    data_type = request.args.get("data_type")
    product_id = request.args.get("product_id")
    price = request.args.get("price")
    seller_id = session['seller_id']
    category_name = request.args.get("category_name")
    product_title = request.args.get("product_title")
    count = cursor.execute("select * from price_request where seller_id ='"+str(seller_id)+"' and product_id= '"+str(product_id)+"' and status='Price requested'")
    if count == 0:
         cursor.execute("insert into price_request(status,price,seller_id,product_id)values('Price requested','"+str(price)+"','"+str(seller_id)+"','"+str(product_id)+"')")
         conn.commit()
    else:
        cursor.execute("update price_request set price='"+str(price)+"' where product_id='"+str(product_id)+"' and seller_id='"+str(seller_id)+"' ")
        conn.commit()
    cursor.execute("select * from price_request where product_id='"+str(product_id)+"' and seller_id='"+str(seller_id)+"'")
    price_requests = cursor.fetchall()
    for price_request in price_requests:
        predicted_price = get_predicted_price_by_product_id(price_request[4])
        if float(price_request[2]) < predicted_price:
            cursor.execute("update price_request set status='Approved' where price_request_id='" + str(price_request[0]) + "'")
            cursor.execute("update products set product_price='"+str(price)+"' where product_id='" + str(price_request[4]) + "'")
            conn.commit()
            return render_template("smessage.html", message="Requested Price Approved")
        else:
            cursor.execute("update price_request set status='Rejected' where price_request_id='" + str(price_request[0]) + "'")
            conn.commit()
            return render_template("smessage.html", message="Requested Price Rejected")
    return redirect("/view_products?category_name=" + category_name + "&product_title=" + product_title+"&data_type="+data_type)


@app.route("/reduce_price")
def reduce_price():
    category_name = request.args.get("category_name")
    product_title = request.args.get("product_title")
    product_id = request.args.get("product_id")
    data_type = request.args.get("data_type")
    price = request.args.get("price")
    return render_template("reduce_price.html", product_id=product_id,category_name=category_name, product_title=product_title, price=price, float=float, data_type=data_type)

@app.route("/reduce_price_action")
def reduce_price_action():
    product_id = request.args.get("product_id")
    price = request.args.get("price")
    category_name = request.args.get("category_name")
    product_title = request.args.get("product_title")
    data_type = request.args.get("data_type")
    cursor.execute("update products set product_price ='"+str(price)+"' where product_id='"+str(product_id)+"'")
    conn.commit()
    return redirect("/view_products?category_name=" + category_name + "&product_title=" + product_title + "&data_type=" + data_type)


@app.route("/view_price_request")
def view_price_request():
    cursor.execute("select * from price_request")
    price_requests = cursor.fetchall()
    return render_template("view_price_request.html", price_requests=price_requests,get_seller_by_seller_id=get_seller_by_seller_id,get_product_by_product_id=get_product_by_product_id, get_predicted_price_by_product_id=get_predicted_price_by_product_id, float=float)

@app.route("/approval")
def approval():
    price_request_id = request.args.get("price_request_id")
    product_price = request.args.get("product_price")
    product_id = request.args.get("product_id")
    query = "update price_request set status='Approved' where price_request_id='"+str(price_request_id)+"'"
    cursor.execute(query)
    query = "update products set product_price='"+str(product_price)+"' where product_id='" + str(product_id) + "'"
    cursor.execute(query)
    print(query)
    conn.commit()
    return redirect("/view_price_request")

@app.route("/reject")
def reject():
    price_request_id = request.args.get("price_request_id")
    cursor.execute("update price_request set status='Rejected' where price_request_id='"+str(price_request_id)+"'")
    conn.commit()
    return redirect("/view_price_request")

@app.route("/remove_from_cart")
def remove_from_cart():
    order_id = request.args.get("order_id")
    order_item_id = request.args.get("order_item_id")
    cursor.execute("delete from order_items where order_item_id='"+str(order_item_id)+"'")
    conn.commit()
    count = cursor.execute("select * from order_items where order_id='"+str(order_id)+"'")
    if count == 0:
        cursor.execute("delete from orders where order_id='"+str(order_id)+"'")
        conn.commit()
        return redirect("/view_orders?view_type=cart")
    else:
        return render_template("message.html", message="Item Removed")

@app.route("/order_now")
def order_now():
    order_id = request.args.get("order_id")
    total_price = request.args.get("total_price")
    return render_template("order_now.html", order_id=order_id, total_price=total_price)




@app.route("/order_now_action")
def order_now_action():
    total_price = request.args.get("total_price")
    order_id = request.args.get("order_id")
    card_type = request.args.get("card_type")
    card_number = request.args.get("card_number")
    name_on_card = request.args.get("name_on_card")
    expire_date = request.args.get("expire_date")
    cvv = request.args.get("cvv")

    cursor.execute("select * from order_items where order_id='" + str(order_id) + "'")
    order_items = cursor.fetchall()

    for order_item in order_items:
        query = "select * from inventory where inventory_id='" + str(order_item[3]) + "' and quantity>=" + str(order_item[1]) + ""
        count = cursor.execute(query)
        if count == 0:
            return render_template("message.html", message="Products out of stock")
        else:
            query = "update inventory set quantity=quantity-'" + str(order_item[1]) + "' where inventory_id='" + str(order_item[3]) + "'"
            cursor.execute(query)
            conn.commit()

    cursor.execute("update orders set status='ordered' where order_id='" + str(order_id) + "'")
    conn.commit()

    cursor.execute("select * from orders where order_id='" + str(order_id) + "'")
    order = cursor.fetchone()
    customer_id = order[4]

    cursor.execute("select * from customers where customer_id='" + str(customer_id) + "'")
    customer = cursor.fetchone()
    email = customer[2]

    message = "Dear Customer,\n\nYour order has been successfully placed. Here are the details:\n\n"
    # total_price = 0

    for order_item in order_items:
        inventory_id = order_item[3]
        cursor.execute("select * from inventory where inventory_id='" + str(inventory_id) + "'")
        inventory = cursor.fetchone()

        product_id = inventory[3]
        cursor.execute("select * from products where product_id='" + str(product_id) + "'")
        product = cursor.fetchone()

        product_name = product[2]
        product_price = float(product[3])
        product_quantity = float(order_item[1])
        # total_price += product_price * product_quantity

        message += f"Product: {product_name}\nQuantity: {product_quantity}\nPrice per unit: {product_price}\n\n"
    message += f"Total Price: {total_price}\n\nThank you for shopping with us!"
    send_email("Your Order Placed Successfully", message, email)
    return render_template("cmessage.html", message="Order Placed")


@app.route("/cancel_order")
def cancel_order():
    order_id = request.args.get("order_id")
    cursor.execute("select * from order_items where order_id='"+str(order_id)+"'")
    order_items = cursor.fetchall()
    for order_item in order_items:
        cursor.execute("update inventory set quantity=quantity+'"+str(order_item[1])+"' where inventory_id='"+str(order_item[3])+"'")
        conn.commit()
    cursor.execute("update orders set status='Cancelled' where order_id='"+str(order_id)+"'")
    conn.commit()
    cursor.execute("select * from orders where order_id='" + str(order_id) + "'")
    order = cursor.fetchone()
    customer_id = (order[4])
    cursor.execute("select * from customers where customer_id='" + str(customer_id) + "'")
    customer = cursor.fetchone()
    email = (customer[2])
    send_email(
        "Your Order Has Been Cancelled",
        "Dear Customer,\n\nWe have received your request to cancel the order. Your order has been successfully cancelled.\n\nThank you for choosing us.",
        email
    )

    return redirect("view_orders?view_type=history")


@app.route("/order_dispatched")
def order_dispatched():
    order_id = request.args.get("order_id")
    cursor.execute("update orders set status='Dispatched' where order_id='"+str(order_id)+"'")
    conn.commit()
    cursor.execute("select * from orders where order_id='" + str(order_id) + "'")
    order = cursor.fetchone()
    customer_id = (order[4])
    cursor.execute("select * from customers where customer_id='" + str(customer_id) + "'")
    customer = cursor.fetchone()
    email = (customer[2])
    send_email(
        "Your Order Has Been Dispatched",
        "Dear Customer,\n\nYour order has been dispatched and is on its way to you. Thank you for shopping with us!",email)
    return redirect("view_orders?view_type=dispatched")


@app.route("/delivered_now")
def delivered_now():
    order_id = request.args.get("order_id")
    cursor.execute("update orders set status ='Delivered' where order_id='"+str(order_id)+"'")
    conn.commit()
    cursor.execute("select * from orders where order_id='" + str(order_id) + "'")
    order = cursor.fetchone()
    customer_id = (order[4])
    cursor.execute("select * from customers where customer_id='" + str(customer_id) + "'")
    customer = cursor.fetchone()
    email = (customer[2])
    send_email(
        "Your Order Has Been Delivered",
        "Dear Customer,\n\nWe are pleased to inform you that your order has been successfully delivered. Thank you for choosing us. We hope you enjoy your purchase!",
        email
    )
    return redirect("/view_orders?view_type=history")


def get_quantity_by_product_id(product_id):
    seller_id = session['seller_id']
    count = cursor.execute("select * from inventory where product_id='"+str(product_id)+"' and seller_id='"+str(seller_id)+"'")
    inventories = cursor.fetchall()
    if count == 0:
        return 0
    return inventories[0][1]

def get_price_by_product_id(product_id):
    seller_id = session['seller_id']
    count = cursor.execute("select * from price_request where product_id='"+str(product_id)+"' and seller_id='"+str(seller_id)+"'")
    price_requests = cursor.fetchall()
    if count == 0:
        return 0, ""
    return price_requests[0][2], price_requests[0][1]

def get_rating_by_product_id(product_id):
    cursor.execute("select avg(review_star_ratings) from ratings where product_id='"+str(product_id)+"'")
    rating = cursor.fetchall()
    return rating[0][0]

def get_predicted_price_by_product_id(product_id):
    cursor.execute("select * from products where product_id='"+str(product_id)+"'")
    products = cursor.fetchall()
    rating = get_rating_by_product_id(product_id)
    cursor.execute("select avg(sentiment_score) from ratings where product_id='"+str(product_id)+"'")
    sentiment_score = cursor.fetchall()
    sentiment_score = sentiment_score[0][0]
    predictions = loaded_model.predict([[sentiment_score, int(products[0][6]), rating]])
    percentage = round(predictions[0],2)
    hike_price = float(products[0][7]) + float(products[0][7]) * percentage/100
    hike_price = round(hike_price,2)
    hike_price = float(hike_price)
    return hike_price

def get_sentiment_score_by_product_id(product_id):
    cursor.execute("select * from products where product_id='"+str(product_id)+"'")
    products = cursor.fetchall()
    rating = get_rating_by_product_id(product_id)
    cursor.execute("select avg(sentiment_score) from ratings where product_id='"+str(product_id)+"'")
    sentiment_score = cursor.fetchall()
    sentiment_score = sentiment_score[0][0]
    sentiment_score = round(sentiment_score,2)
    return sentiment_score

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/notifications")
def notifications():
    customer_id = session['customer_id']
    cursor.execute("select * from notification where customer_id='"+str(customer_id)+"' ")
    notifications=cursor.fetchall()
    print(notifications)
    return render_template("notifications.html",notifications=notifications,get_inventory_id_by_notification=get_inventory_id_by_notification,get_product_id_by_inventory=get_product_id_by_inventory,get_rating_by_product_id=get_rating_by_product_id)


def get_inventory_id_by_notification(inventory_id):
    cursor.execute("select * from inventory where inventory_id='" + str(inventory_id) + "'")
    inventories = cursor.fetchone()
    return inventories


def get_product_id_by_inventory(product_id):
    cursor.execute("select * from products where product_id='" + str(product_id) + "'")
    products = cursor.fetchone()
    return products

app.run(debug=True)