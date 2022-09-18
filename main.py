from flask import Flask, render_template, request
import requests
# from operator import itemgetter
from pprint import pprint

app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/contacts/")
def contacts():
    return render_template('contacts.html')


@app.route("/search/", methods=['GET'])
def search_get():
    return render_template('search.html')


@app.route("/search/", methods=['POST'])
def search_post():
    search_line = request.form['vacancy']
    search_city = request.form['area']
    # ------------------------------------------------------------------------------------------------
    url_api = 'https://api.hh.ru/'
    url_vacancy = f'{url_api}vacancies'

    if search_line != '':
        area_id_all = requests.get('https://api.hh.ru/areas/').json()
        indicator = False
        area_id = 0
        for index_area in range(len(area_id_all)):
            if area_id_all[index_area]['name'] == search_city:
                area_id = area_id_all[index_area]['id']
                indicator = True
                break

        if indicator:
            params = {
                'text': search_line,
                'area': area_id,
                'page': 0
            }
        else:
            params = {
                'text': search_line,
                'page': 0
            }

        result_vacancy = requests.get(url_vacancy, params=params).json()

        if result_vacancy['found'] <= 0:
            all_vacancy = []
        else:
            # pprint(result_vacancy)
            items_vacancy = result_vacancy['items']
            all_vacancy = []
            for item_vacancy in items_vacancy:
                result_url_vacancy = requests.get(item_vacancy['url']).json()
                # pprint(result_url_vacancy)
                print(result_url_vacancy['name'])
                print(result_url_vacancy['area']['name'])
                print(result_url_vacancy['employment']['name'])
                salary = ''
                if result_url_vacancy['salary'] is not None:
                    if result_url_vacancy['salary']['from'] is not None:
                        salary = 'от ' + str(result_url_vacancy['salary']['from'])
                        if result_url_vacancy['salary']['currency'] is not None:
                            salary += str(result_url_vacancy['salary']['currency']) + ' '
                        else:
                            salary += ' '
                    if result_url_vacancy['salary']['to'] is not None:
                        salary = 'до ' + str(result_url_vacancy['salary']['to'])
                        if result_url_vacancy['salary']['currency'] is not None:
                            salary += str(result_url_vacancy['salary']['currency'])
                print(salary)
                result_skill_url_vacancy = result_url_vacancy['key_skills']
                skills = ''

                for index_skill in range(len(result_skill_url_vacancy)):
                    skills = skills + result_skill_url_vacancy[index_skill]['name'] + ', '
                skills = skills[:-2].lower()
                print(skills)
                skills = skills.capitalize()
                print(skills)
                all_vacancy.append([result_url_vacancy['name'],result_url_vacancy['area']['name'],result_url_vacancy['employment']['name'],salary,skills])
    else:
        all_vacancy = []
    # ------------------------------------------------------------------------------------------------

    return render_template('search.html', data=all_vacancy)


if __name__ == "__main__":
    app.run(debug=True)

