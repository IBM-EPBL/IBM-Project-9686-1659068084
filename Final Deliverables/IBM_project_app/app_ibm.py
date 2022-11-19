import numpy as np
import os
from flask import Flask, request, jsonify, render_template,json,redirect,url_for,flash
import pickle
import requests
import sqlite3

# NOTE: you must manually set API_KEY below using information retrieved from your IBM Cloud account.
API_KEY = "okbr7ARnOQjyplTOyvNFC2QVkCF6q7afpci065Hucby8"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
 API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}
app = Flask(__name__)
app.secret_key="21433253"
model = pickle.load(open('rfmodel.pkl', 'rb'))
conn=sqlite3.connect("database1.db")
conn.execute("CREATE TABLE IF NOT EXISTS login(email TEXT PRIMARY KEY,password TEXT)")
conn.close()

@app.route('/')
def main():
    return render_template('login.html')

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        try:
            fv=[x for x in request.form.values()]
            email=request.form["email"]
            pswd=request.form["pswd"]
            conn=sqlite3.connect("database1.db")
            cur=conn.cursor()
            cur.execute("SELECT password FROM login WHERE email=?;",(str(email),))
            result=cur.fetchone()
            cur.execute("SELECT * FROM login")
            if result:
                if result[0]==pswd:
                    flash("login successfully",'success')
                    return redirect('/home')
                else:
                    return render_template("login.html", error="please enter correct password")
                
            else:
                print("register")
                flash("please Register",'danger')
                
                return render_template('register.html',alert="user not found,please register")
            
        except Exception as e:
            return "hello error" 

@app.route('/reg')
def reg():
    return render_template("register.html")

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        try:
            fv=[x for x in request.form.values()]
            email=request.form["email"]
            pswd=request.form["pswd"]
            conn=sqlite3.connect("database1.db")
            cur=conn.cursor()
            cur.execute("SELECT * FROM login WHERE email=?;",(str(email),))
            result=cur.fetchone()
            if result:
                flash("user already exist,please login",'danger')
                return render_template('login.html',alert="user already exist,please login")
            else:
                cur.execute("INSERT INTO  login(email,password)values(?,?)",(str(email),str(pswd)))
                conn.commit()
                cur.execute("SELECT * FROM login")
                flash("Registered successfully",'success')
                return render_template('login.html',message="Registered successfully,please login")
            
        except Exception as e:
            print(e)
            #flash(e,'danger')
            return "hello error1"
        
            
                #return redirect('/')
   # return render_template('login.html')
@app.route('/home')
def home():
    return render_template('mainpage.html')

@app.route('/predict',methods=['POST'])
def predict():
    '''
    For rendering results on HTML GUI
    '''
    sm=[6,7,8]
    wt=[9,10,11]
    sp=[12,1,2,3]
    fl=[4,5]
    farr= [int(x) for x in request.form.values()]
    if farr[1] in sm:
        farr.append(0)
    elif farr[1] in wt:
        farr.append(1)
    elif farr[1] in sp:
        farr.append(2)
    else:
        farr.append(3)
    final_features=[int(x) for x in farr]
    print(final_features)
    payload_scoring = {"input_data": [{"fields": [['QUARTER','MONTH','DAY_OF_MONTH','DAY_OF_WEEK','FL_NUM','ORIGIN','DEST','CRS_DEP_TIME.1','CRS_ARR_TIME.1','CRS_ELAPSED_TIME','DISTANCE','SEASON']], "values": [final_features]}]}

    response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/b54f9857-1352-432a-8ab1-144ebda20501/predictions?version=2022-11-08', json=payload_scoring,headers={'Authorization': 'Bearer ' + mltoken})
    print("Scoring response")
    pred=response_scoring.json()
    print(pred)
    prediction=pred['predictions'][0]['values'][0][0]
    #prediction = model.predict([final_features])
    print(prediction)

    output =prediction

    if output==0:
        return render_template('result.html', prediction_text='No delay will happen {}'.format(output))
    elif output==1:
        return render_template('result.html', prediction_text='There is a chance to departure delay will happen {}'.format(output))
    elif output==2:
        return render_template('result.html', prediction_text='here is a chance to both departure and arrival delay will happen {}'.format(output))
    elif output==3:
        return render_template('result.html', prediction_text='here is a chance to flight  will diverted {}'.format(output))
    elif output==4:
        return render_template('result.html', prediction_text='here is a chance to cancel the flight {}'.format(output))
    else:
        return render_template('result.html', prediction_text='output {}'.format(output))
'''@app.route('/predict_api',methods=['POST'])
def predict_api():
    
    For direct API calls trought request
    
    data = request.get_json(force=True)
    prediction = model.predict([np.array(list(data.values()))])

    output = prediction[0]
    return jsonify(output)'''

if __name__ == "__main__":
    os.environ.setdefault('FLASK_ENV', 'development')
    app.run(debug=False)