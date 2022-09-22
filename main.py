from flask import Flask, render_template, request
import requests
from pprint import pprint
import sqlite3

app = Flask(__name__)


def checking_table(cur, table, column, variable):
    sql_str = 'select id from ' + table + ' where ' + column + ' = "' + str(variable) + '"'
    cur.execute(sql_str)
    if len(list(cur.execute(sql_str))) == 0:
        sql_str1 = 'INSERT INTO ' + table + ' (' + column + ') VALUES ("' + variable + '")'
        cur.execute(sql_str1)
    return list(cur.execute(sql_str))[0][0]


def checking_variable(result_url, branch1, branch2):
    if branch2 == 0:
        if result_url['' + branch1 + ''] is not None:
            variable = str(result_url['' + branch1 + ''])
        else:
            variable = '---'
    else:
        if result_url['' + branch1 + ''] is not None:
            if result_url['' + branch1 + '']['' + branch2 + ''] is not None:
                variable = str(result_url['' + branch1 + '']['' + branch2 + ''])
            else:
                variable = '---'
        else:
            variable = '---'
    return variable


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
    search_country = request.form['area']
    # ------------------------------------------------------------------------------------------------
    url_api = 'https://api.hh.ru/'
    url_vacancy = f'{url_api}vacancies'

    if search_line != '':
        area_id_all = requests.get('https://api.hh.ru/areas/').json()
        indicator = False
        area_id = 0
        for index_area in range(len(area_id_all)):
            if area_id_all[index_area]['name'] == search_country:
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
            con = sqlite3.connect("hh.sqlite3")
            cur = con.cursor()
            sql_str = 'select num_search from dif_variable'
            cur.execute(sql_str)
            num_search = list(cur.fetchone())[0] + 1
            sql_str = 'update dif_variable set num_search = "' + str(num_search) + '"'
            cur.execute(sql_str)
            con.commit()

            items_vacancy = result_vacancy['items']
            for item_vacancy in items_vacancy:
                result_url_vacancy = requests.get(item_vacancy['url']).json()
                vacancy_id = result_url_vacancy['id']
                sql_str = 'select id from save_data where vacancy_id = ' + str(vacancy_id)

                if len(list(cur.execute(sql_str))) == 0:

                    variable = checking_variable(result_url_vacancy, 'name', 0)
                    v_id = checking_table(con, 'vacancy', 'name', variable)
                    con.commit()

                    variable = checking_variable(result_url_vacancy, 'area', 'name')
                    r_id = checking_table(con, 'region', 'name', variable)
                    con.commit()

                    variable = checking_variable(result_url_vacancy, 'employment', 'name')
                    e_id = checking_table(con, 'employment', 'type', variable)
                    con.commit()

                    variable = checking_variable(result_url_vacancy, 'salary', 'currency')
                    c_id = checking_table(con, 'currency', 'currency', variable)
                    con.commit()

                    s_from = checking_variable(result_url_vacancy, 'salary', 'from')
                    s_to = checking_variable(result_url_vacancy, 'salary', 'to')

                    sql_str = 'INSERT INTO save_data (vacancy_id, v_id, r_id, e_id, c_id, s_from, s_to, num_search) ' \
                              'VALUES ("' + str(vacancy_id) + '", "' + str(v_id) + '", "' + str(r_id) + '", "' + str(e_id) + '", "' \
                              + str(c_id) + '", "' + str(s_from) + '", "' + str(s_to) + '", "' + str(num_search) + '")'
                    cur.execute(sql_str)
                    con.commit()

                    sd_id = checking_table(con, 'save_data', 'vacancy_id', vacancy_id)

                    result_skill_url_vacancy = result_url_vacancy['key_skills']
                    print(result_skill_url_vacancy)
                    for index_skill in range(len(result_skill_url_vacancy)):
                        variable = result_skill_url_vacancy[index_skill]['name']
                        if variable == '':
                            variable = '---'
                        s_id = checking_table(con, 'skills', 'skill', variable)
                        con.commit()
                        sql_str2 = 'INSERT INTO sd_id_skills (sd_id, skills_id) VALUES ("' + str(sd_id) + '", "' + str(s_id) + '")'
                        cur.execute(sql_str2)
                        con.commit()

                else:
                    sql_str = 'select id from save_data where vacancy_id = ' + str(result_url_vacancy['id'])
                    cur.execute(sql_str)
                    sd_id = list(cur.fetchone())[0]
                    sql_str = 'update save_data set num_search = "' + str(num_search) + '" where id = "' + str(sd_id) + '"'
                    cur.execute(sql_str)
                    con.commit()

            # вывод данных и базы
            sql_str = 'select v.name, r.name, e.type, c.currency, save_data.s_from, save_data.s_to, ' \
                      'GROUP_CONCAT''(''skills.skill'')'' as skill_name ' \
                      'from vacancy v, region r, employment e, currency c, ' \
                      'save_data LEFT JOIN sd_id_skills ' \
                      'ON save_data.id = sd_id_skills.sd_id ' \
                      'LEFT JOIN skills ' \
                      'ON skills.id = sd_id_skills.skills_id ' \
                      'where save_data.v_id=v.id and save_data.r_id=r.id and save_data.e_id=e.id and ' \
                      'save_data.c_id=c.id and save_data.num_search = "' + str(num_search) + '" GROUP BY save_data.id'

            cur.execute(sql_str)
            all_vacancy = cur.fetchall()
            # pprint(all_vacancy)

    else:
        all_vacancy = []
    # ------------------------------------------------------------------------------------------------

    return render_template('search.html', data=all_vacancy)


if __name__ == "__main__":
    app.run(debug=True)

