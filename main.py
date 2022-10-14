from flask import Flask, render_template, request
import requests
from pprint import pprint
from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


app = Flask(__name__)
engine = create_engine('sqlite:///orm_db.sqlite', echo=True)
Base = declarative_base()
metadata = MetaData()


class Save_data(Base):
    __tablename__ = 'save_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vacancy_id = Column(Integer, unique=True)
    v_id = Column(Integer, ForeignKey('vacancy.id'))
    r_id = Column(Integer, ForeignKey('region.id'))
    e_id = Column(Integer, ForeignKey('employment.id'))
    c_id = Column(Integer, ForeignKey('currency.id'))
    s_from = Column(Integer)
    s_to = Column(Integer)
    num_search = Column(Integer)

    def __init__(self, vacancy_id, v_id, r_id, e_id, c_id, s_from, s_to, num_search):
        self.vacancy_id = vacancy_id
        self.v_id = v_id
        self.r_id = r_id
        self.e_id = e_id
        self.c_id = c_id
        self.s_from = s_from
        self.s_to = s_to
        self.num_search = num_search

    def __str__(self):
        return f'{self.id} {self.vacancy_id}  {self.v_id}  {self.r_id}  {self.e_id}  {self.c_id}  {self.s_from}  {self.s_to} {self.num_search}'


class Sd_id_skills(Base):
    __tablename__ = 'sd_id_skills'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sd_id = Column(Integer, ForeignKey('save_data.id'))
    skills_id = Column(Integer, ForeignKey('skills.id'))

    def __init__(self, sd_id, skills_id):
        self.sd_id = sd_id
        self.skills_id = skills_id

    def __str__(self):
        return f'{self.id} {self.sd_id} {self.skills_id}'


class Currency(Base):
    __tablename__ = 'currency'
    id = Column(Integer, primary_key=True, autoincrement=True)
    currency = Column(String, unique=True)

    def __init__(self, currency):
        self.currency = currency

    def __str__(self):
        return f'{self.id} {self.currency}'


class Dif_variable(Base):
    __tablename__ = 'dif_variable'
    id = Column(Integer, primary_key=True)
    num_search = Column(Integer)

    def __init__(self, num_search):
        self.num_search = num_search

    def __str__(self):
        return f'{self.id} {self.num_search}'


class Employment(Base):
    __tablename__ = 'employment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, unique=True)

    def __init__(self, type):
        self.type = type

    def __str__(self):
        return f'{self.id} {self.type}'


class Region(Base):
    __tablename__ = 'region'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'{self.id} {self.name}'


class Skills(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill = Column(String, unique=True)

    def __init__(self, skill):
        self.skill = skill

    def __str__(self):
        return f'{self.id} {self.skill}'


class Vacancy(Base):
    __tablename__ = 'vacancy'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'{self.id} {self.name}'


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
            Session = sessionmaker(bind=engine)
            session = Session()

            if session.query(Dif_variable).count() == 0:
                variable = Dif_variable(0)
                session.add(variable)
                session.commit()

            num_search = session.query(Dif_variable).first().num_search + 1
            session.query(Dif_variable).filter_by(id=1).update({'num_search': num_search})
            session.commit()

            items_vacancy = result_vacancy['items']
            for item_vacancy in items_vacancy:
                result_url_vacancy = requests.get(item_vacancy['url']).json()
                vacancy_id = result_url_vacancy['id']

                if session.query(Save_data).filter_by(vacancy_id=vacancy_id).count() == 0:
                    variable = checking_variable(result_url_vacancy, 'name', 0)
                    if session.query(Vacancy).filter_by(name=variable).count() == 0:
                        new_data = Vacancy(variable)
                        session.add(new_data)
                        session.commit()
                    v_id = session.query(Vacancy).filter_by(name=variable).first().id

                    variable = checking_variable(result_url_vacancy, 'area', 'name')
                    if session.query(Region).filter_by(name=variable).count() == 0:
                        new_data = Region(variable)
                        session.add(new_data)
                        session.commit()
                    r_id = session.query(Region).filter_by(name=variable).first().id

                    variable = checking_variable(result_url_vacancy, 'employment', 'name')
                    if session.query(Employment).filter_by(type=variable).count() == 0:
                        new_data = Employment(variable)
                        session.add(new_data)
                        session.commit()
                    e_id = session.query(Employment).filter_by(type=variable).first().id

                    variable = checking_variable(result_url_vacancy, 'salary', 'currency')
                    if session.query(Currency).filter_by(currency=variable).count() == 0:
                        new_data = Currency(variable)
                        session.add(new_data)
                        session.commit()
                    c_id = session.query(Currency).filter_by(currency=variable).first().id

                    s_from = checking_variable(result_url_vacancy, 'salary', 'from')
                    s_to = checking_variable(result_url_vacancy, 'salary', 'to')

                    new_data = Save_data(vacancy_id, v_id, r_id, e_id, c_id, s_from, s_to, num_search)
                    session.add(new_data)
                    session.commit()

                    if session.query(Save_data).filter_by(vacancy_id=vacancy_id).count() == 0:
                        new_data = Save_data(vacancy_id)
                        session.add(new_data)
                        session.commit()
                    sd_id = session.query(Save_data).filter_by(vacancy_id=vacancy_id).first().id

                    result_skill_url_vacancy = result_url_vacancy['key_skills']
                    for index_skill in range(len(result_skill_url_vacancy)):
                        variable = result_skill_url_vacancy[index_skill]['name']
                        if variable == '':
                            variable = '---'

                    if session.query(Skills).filter_by(skill=variable).count() == 0:
                        new_data = Skills(variable)
                        session.add(new_data)
                        session.commit()
                    s_id = session.query(Skills).filter_by(skill=variable).first().id

                    new_data = Sd_id_skills(sd_id, s_id)
                    session.add(new_data)
                    session.commit()

                else:
                    sd_id = session.query(Save_data).filter_by(vacancy_id=result_url_vacancy['id']).first().id
                    session.query(Save_data).filter_by(id=sd_id).update({'num_search': num_search})
                    session.commit()

            # вывод данных из базы
            # sql_str = 'select v.name, r.name, e.type, c.currency, save_data.s_from, save_data.s_to, ' \
            #           'GROUP_CONCAT''(''skills.skill'')'' as skill_name ' \
            #           'from vacancy v, region r, employment e, currency c, ' \
            #           'save_data LEFT JOIN sd_id_skills ' \
            #           'ON save_data.id = sd_id_skills.sd_id ' \
            #           'LEFT JOIN skills ' \
            #           'ON skills.id = sd_id_skills.skills_id ' \
            #           'where save_data.v_id=v.id and save_data.r_id=r.id and save_data.e_id=e.id and ' \
            #           'save_data.c_id=c.id and save_data.num_search = "' + str(num_search) + '" GROUP BY save_data.id'
            # cur.execute(sql_str)
            # all_vacancy = cur.fetchall()

            query = session.query(Save_data.num_search, Vacancy.name, Region.name, Employment.type, Currency.currency, Save_data.s_from, Save_data.s_to
                                ).filter(
                                Save_data.num_search == num_search
                                ).filter(
                                Vacancy.id == Save_data.v_id
                                ).filter(
                                Region.id == Save_data.r_id
                                ).filter(
                                Employment.id == Save_data.e_id
                                ).filter(
                                Currency.id == Save_data.c_id
                                ).all()

            print('*'*50)
            pprint(query)
            print('*' * 50)
            print('*' * 50)

            all_vacancy = query
    else:
        all_vacancy = []

    return render_template('search.html', data=all_vacancy)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    app.run(debug=True)

