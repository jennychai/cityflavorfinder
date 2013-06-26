from flask import Flask
@app.route("/text.json")
def textjson():
	#look up in the data base make it into json and return to html to display
	request.args.get('query','insight') + "ism' #'query' is the default

	d = {"text": text}
	return jsonify(d)

