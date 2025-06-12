from flask import Flask, render_template, request
import requests
import sqlite3
from datetime import datetime
import urllib.parse
import csv
from flask import Response, jsonify

app = Flask(__name__)


API_KEY = 'b21655887f6688f43fc01ddc353294de' 
YOUTUBE_API_KEY = 'AIzaSyBxNYCNHVTHgucW0lRGPL1DvG2_4co3IWM'


@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    video_links = []
    map_url = ""

    if request.method == 'POST':
        location = request.form['location']
        url = f'https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={API_KEY}&units=metric'
        response = requests.get(url)

        if response.status_code == 200:
            weather_data = response.json()
            first_result = weather_data['list'][0]
            temp = first_result['main']['temp']
            desc = first_result['weather'][0]['description']
            dt = first_result['dt_txt']

            # Save to DB
            conn = sqlite3.connect('weather.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO weather (location, datetime, temperature, description)
                VALUES (?, ?, ?, ?)
            ''', (location, dt, temp, desc))
            conn.commit()
            conn.close()

            # YouTube API
            YOUTUBE_API_KEY = 'AIzaSyBxNYCNHVTHgucW0lRGPL1DvG2_4co3IWM'
            search_query = f"{location} weather travel guide"
            encoded_query = urllib.parse.quote(search_query)
            youtube_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=3&q={encoded_query}&key={YOUTUBE_API_KEY}"

            yt_response = requests.get(youtube_url)
            if yt_response.status_code == 200:
                yt_data = yt_response.json()
                for item in yt_data['items']:
                    if item['id']['kind'] == 'youtube#video':
                        video_id = item['id']['videoId']
                        video_links.append(f"https://www.youtube.com/embed/{video_id}")

            # Free Map Embed
            map_url = f"https://maps.google.com/maps?q={urllib.parse.quote(location)}&output=embed"

    return render_template('index.html', weather=weather_data, video_links=video_links, map_url=map_url)


        
@app.route('/history')
def history():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM weather')
    records = cursor.fetchall()
    conn.close()
    return render_template('history.html', records=records)

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM weather WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return "Record deleted successfully. <a href='/history'>Go back</a>"

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        location = request.form['location']
        temperature = request.form['temperature']
        description = request.form['description']
        datetime_val = request.form['datetime']
        
        cursor.execute('''
            UPDATE weather SET location = ?, temperature = ?, description = ?, datetime = ?
            WHERE id = ?
        ''', (location, temperature, description, datetime_val, id))
        conn.commit()
        conn.close()
        return "Record updated successfully. <a href='/history'>Go back</a>"
    else:
        cursor.execute('SELECT * FROM weather WHERE id = ?', (id,))
        record = cursor.fetchone()
        conn.close()
        return render_template('update.html', record=record)

@app.route('/export/csv')
def export_csv():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM weather')
    records = cursor.fetchall()
    conn.close()

    output = "ID,Location,Datetime,Temperature,Description\n"
    for row in records:
        output += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n"

    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=weather_data.csv"})

@app.route('/export/json')
def export_json():
    conn = sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM weather')
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "location": row[1],
            "datetime": row[2],
            "temperature": row[3],
            "description": row[4]
        })
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
