from app import application
from flask import jsonify, Response, session
from app.models import *
from app import *
import uuid
import datetime
from marshmallow import Schema, fields
from flask_restful import Resource, Api
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs
import json

class SignUpRequest(Schema):
    username = fields.Str(default = "username")
    password = fields.Str(default = "password")
    name = fields.Str(default = "name")
    level = fields.Int(default = 0)

class LoginRequest(Schema):
    username = fields.Str(default="username")
    password = fields.Str(default="password")

class AddVendorRequest(Schema):
    user_id = fields.Str(default="user_id")

class VendorsListResponse(Schema):
    vendors=fields.List(fields.Dict())

class AddItemRequest(Schema):
    item_id = fields.Str(default="item_id")
    item_name = fields.Str(default="item_name")
    restaurant_name = fields.Str(default="restaurant_name")
    available_quantity = fields.Str(default=0)
    unit_price = fields.Str(default=0)
    calories_per_gm  = fields.Str(default=0)

class ItemsListResponse(Schema):
    items=fields.List(fields.Dict())

class ItemOrderList(Schema):
    order_id = fields.Str(default="order_id")
    quantity = fields.Str(default=0)

class PlaceOrderRequest(Schema):
    customer_id = fields.List(default="customer_id")
    vendor_id = fields.Str(default="vendor_id")
    item_id = fields.Str(default="item_id")
    quantity = fields.Str(default=0)

class APIResponse(Schema):
    message = fields.Str(default="Success")

class ListOrderResponse(Schema):
    orders = fields.List(fields.Dict())

#  Restful way of creating APIs through Flask Restful
class SignUpAPI(MethodResource, Resource):
    @doc(description='Sign Up API', tags=['SignUp API'])
    @use_kwargs(SignUpRequest,location=('json'))
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            user=User(
                uuid.uuid4(),
                kwargs['name'],
                kwargs['username'],
                kwargs['password'],
                kwargs['level'],
                1,
                datetime.datetime.utcnow())
            db.session.add(user)
            db.session.commit()
            return jsonify({'message':'User successfully registered'}),200
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Not able to register user:{str(e)}'}),400
            
api.add_resource(SignUpAPI, '/signup')
docs.register(SignUpAPI)

class LoginAPI(MethodResource, Resource):
    @doc(description='Login API',tags=['Login API'])
    @use_kwargs(LoginRequest,location={'json'})
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            user=User.query.filter_by(username=kwargs['username'], password=kwargs['password']).first()
            if user:
                user_type=User.query.filter_by(user_id=session['user_id']).first().level
                if user_type==0:
                    print('User Login Successful')
                elif user_type==1:
                    print('Vendor login Successful')
                elif user_type==2:
                    print('Admin login Successful')
                session['user_id']= user.user_id
                print(f'User id:{str(session["user_id"])}')
                return jsonify({'message':'User successfully logged in'}),200
            else:
                return jsonify({'message':'User not found'}),404
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Not able to login user:{str(e)}'}),400


api.add_resource(LoginAPI, '/login')
docs.register(LoginAPI)

class LogoutAPI(MethodResource, Resource):
    @doc(description='Logout API',tags=['Logout API'])
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['user_id']:
                session['user_id']= None
                print('Logged out Successful')
                return jsonify({'message':'User successfully logged out'}),200
            else:
                print('user not found')
                return jsonify({'message':'User is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Not able to logout user:{str(e)}'}),400
            

api.add_resource(LogoutAPI, '/logout')
docs.register(LogoutAPI)


class AddVendorAPI(MethodResource, Resource):
    @doc(description='Add Vendor API',tags=['Vendor API'])
    @use_kwargs(AddVendorRequest,location={'json'})
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['user_id']:
                user_id = session['user_id']
                user_type=User.query.filter_by(user_id=session['user_id']).first().level
                print(user_id)
                if user_type==2:
                    vendors_user_id = kwargs['user_id']  
                    user=User.query.filter_by(user_id=vendors_user_id).first()
                    user.level=1
                    db.session.commit()
                    return jsonify({'message':'Vendor successfully added'}),200
                else:
                    return jsonify({'message':'Logged in user is not admin'}),401
            else:
                return jsonify({'message':'User is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Not able to add vendor:{str(e)}'}),400
            

api.add_resource(AddVendorAPI, '/add_vendor')
docs.register(AddVendorAPI)


class GetVendorsAPI(MethodResource, Resource):
    @doc(description='Get Vendor API',tags=['Vendor API'])
    @marshal_with(VendorsListResponse)
    def get(self):
        try:
            if session['user_id']:
                user_id=session['user_id']
                user_type = User.query.filter_by(user_id = user_id).first().level
                print(user_id)
                if user_type==2:
                    vendors=User.query.filter_by(level=1)
                    vendors_list=list()
                    for vendor in vendors:
                        vendor_dict={}
                        vendor_dict['vendor_id']=vendor.user_id
                        vendor_dict['name']= vendor.name
                        vendors_list.append(vendor_dict)
                    return VendorsListResponse().dump(dict(vendors=vendors_list)),200
                else:
                    return jsonify({'message':'Logged in user is not admin'}),405
            else:
                return jsonify({'message':'User is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Not able to get vendor list:{str(e)}'}),400
            

api.add_resource(GetVendorsAPI, '/list_vendors')
docs.register(GetVendorsAPI)

class AddItemAPI(MethodResource, Resource):
    @doc(description='Add Item API',tags=['Items API'])
    @use_kwargs(AddItemRequest,location={'json'})
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['user_id']:
                user_id=session['user_id']
                user_type = User.query.filter_by(user_id=user_id).first().level
                print(user_id)
                print(user_type)
                if user_type==1:
                    item= Item(
                        uuid.uuid4(),
                        kwargs['item_id'],
                        kwargs['item_name'],
                        kwargs['restaurant_name'],
                        kwargs['available_quantity'],
                        kwargs['unit_price'],
                        kwargs['calories_per_gm'])
                    db.session.add(item)
                    db.session.commit()                 
                    return jsonify({'message': 'Items added successfully'}),200
                else:
                    return jsonify({'message': 'Logged in user is not vendor'}),405
            else:
                return jsonify({'message':'Vendor is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Unable to add item:{str(e)}'}),400
            
api.add_resource(AddItemAPI, '/add_item')
docs.register(AddItemAPI)


class ListItemsAPI(MethodResource, Resource):
    @doc(description='List Items API',tags=['Items API'])
    @marshal_with(ItemsListResponse)
    def get(self):
        try:
            if session['user_id']:
                items=Item.query.all()
                items_list=list()
                for item in items:
                    item_dict={}
                    item_dict['item_id'] = item.item_id
                    item_dict['item_name'] = item.item_name
                    item_dict['restaurant_name'] = item.restaurant_name
                    item_dict['available_quantity'] = item.available_quantity
                    item_dict['unit_price'] = item.unit_price
                    item_dict['calories_per_gm'] = item.calories_per_gm

                    items_list.append(item_dict),
                    print(items_list)
                return ItemsListResponse().dump(dict(items=items_list)),200
            else:
                print('user not found')
                return jsonify({'message':'User is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Unable to list items:{str(e)}'}),401

api.add_resource(ListItemsAPI, '/list_items')
docs.register(ListItemsAPI)


class CreateItemOrderAPI(MethodResource, Resource):
    @doc(description='Create Item Order API',tags=['Order API'])
    @use_kwargs(ItemOrderList,location={'json'})
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['user_id']:
                user_id=session['user_id']
                user_type = User.query.filter_by(user_id=user_id).first().level
                if user_type==0:
                    order_id=uuid.uuid4()
                    order = Order(order_id,user_id)
                    db.session.add(order)
                    for item in kwargs['items']:
                        item=dict(item)
                        order_item=OrderItems(
                            uuid.uuid4(),
                            order_id,
                            item['item_id'],
                            item['quantity'])
                        db.session.add(order_item)
                    db.session.commit()                 
                    return APIResponse().dump(
                        dict(message=f'Items added successfully to the order list:{order_id}')), 200
                else:
                    return jsonify({'message': 'Logged in user is not customer'}),405
            else:
                return jsonify({'message':'customer is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Unable to add items to the order list:{str(e)}'}),400
            

api.add_resource(CreateItemOrderAPI, '/create_items_order')
docs.register(CreateItemOrderAPI)


class PlaceOrderAPI(MethodResource, Resource):
    @doc(description='Place Order API',tags=['Order API'])
    @use_kwargs(PlaceOrderRequest,location={'json'})
    @marshal_with(APIResponse)
    def post(self, **kwargs):
        try:
            if session['user_id']:
                user_id=session['user_id']
                user_type = User.query.filter_by(user_id=user_id).first().level
                if user_type==0:
                    order_items= User.query.filter_by(order_id=kwargs['order_id'],is_active=1)
                    order=Order.query.filter_by(order_id=kwargs['order_id'],is_active=1).first()
                    total_amount=0
                    for order_item in order_items:
                        item_id=order_item.order_id
                        quantity=order_item.quantity
                        item=Item.query.filter_by(item_id=item_id, is_active=1).first()
                        total_amount += quantity*item.unit_price
                        print(total_amount)
                        item.available_quantity = item.available_quantity - quantity
                        order.total_amount = total_amount
                        order.is_placed=1                   
                        db.session.commit()                 
                    return jsonify({'message': 'Order placed added successfully'}),200
                else:
                    return jsonify({'message': 'Logged in user is not customer'}),405
            else:
                return jsonify({'message':'Customer is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Unable to place order:{str(e)}'}),400
            

api.add_resource(PlaceOrderAPI, '/place_order')
docs.register(PlaceOrderAPI)

class ListOrdersByCustomerAPI(MethodResource, Resource):
    @doc(description='List Orders By Customer API',tags=['Order API'])
    @marshal_with(ListOrderResponse)
    def get(self, **kwargs):
        try:
            if session['user_id']:
                user_id = session['user_id'] 
                user_type = User.query.filter_by(user_id=user_id).first().level
                if user_type==0:
                    orders = Order.query.filter_by(user_id=user_id, is_active=1)
                    order_list=list()
                    for order in orders:
                        order_items=OrderItems.query.filter_by(order_id=order.order_id,is_active=1)
                        order_dict = {}
                        order_dict['order_id']=order.order_id
                        order_dict['items'] = list()
                        for order_item in order_items:
                            order_item_dict={}
                            order_item_dict['item_id']=order_item.item_id
                            order_item_dict['quantity']=order_item.quantity
                            order_dict['items'].append(order_item_dict)
                        order_list.append(order_dict)
                    return ListOrderResponse().dump(dict(order=order_list)),200
                else:
                    return jsonify({'message': 'Logged in user is not customer'}),405
            else:
                return jsonify({'message':'customer is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Unable to list orders :{str(e)}'}),400
            

api.add_resource(ListOrdersByCustomerAPI, '/list_orders')
docs.register(ListOrdersByCustomerAPI)


class ListAllOrdersAPI(MethodResource, Resource):
    @doc(description='List All Orders API',tags=['Order API'])
    @marshal_with(ListOrderResponse)
    def get(self, **kwargs):
        try:
            if session['user_id']:
                user_id=session['user_id']
                user_type = User.query.filter_by(user_id=user_id).first().level
                if user_type==2:
                    orders = Order.query.filter_by(is_active=1)
                    order_list=list()
                    for order in orders:
                        order_items=OrderItems.query.filter_by(order_id=order.order_id,is_active=1)
                        order_dict = {}
                        order_dict['order_id']=order.order_id
                        order_dict['items'] = list()
                        for order_item in order_items:
                            order_item_dict={}
                            order_item_dict['item_id']=order_item.item_id
                            order_item_dict['quantity']=order_item.quantity
                            order_dict['items'].append(order_item_dict)
                        order_list.append(order_dict)
                    return ListOrderResponse().dump(dict(orders=order_list)),200
                else:
                    return jsonify({'message': 'Logged in user does not have admin rights'}),405
            else:
                return jsonify({'message':'Admin is not logged in'}),401
        except Exception as e:
            print(str(e))
            return jsonify({'message':f'Unable to list all orders:{str(e)}'}),400
            
api.add_resource(ListAllOrdersAPI, '/list_all_orders')
docs.register(ListAllOrdersAPI)