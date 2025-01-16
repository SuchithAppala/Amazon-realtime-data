drop database Amazon_realtime_data;
create database Amazon_realtime_data;
use Amazon_realtime_data;
create table sellers(
	seller_id int auto_increment primary key,
	name VARCHAR(255) not null, 
	email  VARCHAR(255) not null unique,
	phone  VARCHAR(255) not null unique,
    address  VARCHAR(255) not null,
	password VARCHAR(255) not null,
	status VARCHAR(255) default 'Not Verified'
);

create table customers(
	customer_id int auto_increment primary key,
	name  VARCHAR(255) not null,
	email  VARCHAR(255) not null unique,
	phone  VARCHAR(255) not null unique,
	address VARCHAR(255) not null,
	password VARCHAR(255) not null
);

create table products(
	product_id int auto_increment primary key,
    asin varchar(255),
    product_title varchar(255),
    product_price varchar(255),
	product_photo varchar(255),
    category varchar(255),
    rankk varchar(255),
	original_price varchar(255),
    data_type varchar(255) default 'csv'
);

create table ratings(
	rating_id int auto_increment primary key,
	review_comment text not null,
    review_title text not null,
    review_star_ratings varchar(255),
	review_date varchar(255) not null,
	number_people_helpfull varchar(255) not null,
	sentiment varchar(255) not null,
    sentiment_score varchar(255) not null,
    product_id int,
    foreign key (product_id) references products (product_id)
);
   
create table tags(
	tag_id int auto_increment primary key,
    tag varchar(255),
	rating_id int,
    foreign key (rating_id) references ratings (rating_id)
   );
  
  create table inventory(
	inventory_id int auto_increment primary key,
    quantity varchar(255) not null,
    seller_id int,
    product_id int,
	foreign key (seller_id) references sellers (seller_id),
	foreign key (product_id) references products (product_id) 

);

create table orders(
	order_id int auto_increment primary key,
	status varchar(255) not null,
	date datetime not null default current_timestamp,
	seller_id int,
	customer_id int,
	foreign key (customer_id) references customers (customer_id), 
    foreign key (seller_id) references sellers (seller_id) 
);

create table order_items(
	order_item_id int auto_increment primary key,
    quantity varchar(255) not null,
	order_id int,
    inventory_id int,
	foreign key (inventory_id) references inventory (inventory_id), 
	foreign key (order_id) references orders (order_id) 
);


create table price_request(
	price_request_id int auto_increment primary key,
	status VARCHAR(255) default 'Price requested',
	price varchar(255),
	seller_id int,
	product_id int,
	foreign key (product_id) references products (product_id), 
    foreign key (seller_id) references sellers (seller_id) 
);
create table notification(
	notification_id int auto_increment primary key,
	status VARCHAR(255) default 'Not Notified',
    quantity int,
	inventory_id int,
    customer_id int,
	foreign key (inventory_id) references inventory(inventory_id), 
    foreign key (customer_id) references customers(customer_id) 
);
