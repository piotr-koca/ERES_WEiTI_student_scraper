# -*- coding: utf-8 -*-
import httplib2
import jsonpickle
import os
from datetime import datetime
from bs4 import BeautifulSoup, SoupStrainer


class Result(object):
    def __init__(self):
        self.students = []
        self.timestamp = ''


class Lecture(object):
    def __init__(self):
        self.name = ''
        self.students = []


class Student(object):
    def __init__(self):
        self.number = ''
        self.surname = ''
        self.names = ''
        self.lectures = []
        self.mail = ''
        self.spec = ''


def get_urls():

    urls = [
        'http://eres.elka.pw.edu.pl/eres/wzapwkl$kla.QueryViewByKey?P_ID_KLASY=OT&Z_CHK=51370',
        'http://eres.elka.pw.edu.pl/eres/wzapwkl$kla.QueryViewByKey?P_ID_KLASY=DYPLB&Z_CHK=27587',
        'http://eres.elka.pw.edu.pl/eres/wzapwkl$kla.QueryViewByKey?P_ID_KLASY=DYPLU&Z_CHK=32451',
        'http://eres.elka.pw.edu.pl/eres/wzapwkl$kla.QueryViewByKey?P_ID_KLASY=NES&Z_CHK=61442',
        'http://eres.elka.pw.edu.pl/eres/wzapwkl$kla.QueryViewByKey?P_ID_KLASY=JOO&Z_CHK=58390',
    ]

    print('Using following urls to obtain available classes:')
    for url in urls:
        print(url)
    print('')

    return urls


def get_content(url):

    http = httplib2.Http(timeout=10)
    response, content = http.request(url)

    if response.status == 200:

        return content.decode('iso-8859-2').encode('utf-8')

    else:
        return None


def get_lectures_urls(url):

    html = get_content(url)

    urls = []
    for a in BeautifulSoup(html, 'html.parser', parse_only=SoupStrainer('a')):
        if a.has_attr('href') and 'QueryViewByKey' in a['href']:
            u = 'http://eres.elka.pw.edu.pl/eres/' + a['href']
            urls.append(u)

    return urls


def get_lecture_students(html):

    students = []

    bs = BeautifulSoup(html, "lxml")

    trs = bs.findAll("tr", {"class": "cgrldatarow"})

    for tr in trs:

        student = Student()

        student_enrolled = False

        tr_children = tr.findChildren()
        for child in tr_children:

            if not child.has_attr('id'):
                continue

            if 'NAZWISKO' in child['id']:
                student.surname = str(child.getText().encode('utf8'))

            if 'IMIONA' in child['id']:
                student.names = str(child.getText().encode('utf8'))

            if 'NR_ALBUMU' in child['id']:
                student.number = str(child.getText().encode('utf8'))

            if 'ID_SPECJALNOSCI' in child['id']:
                student.spec = str(child.getText().encode('utf8'))

            if 'STATUS_ZAPISU' in child['id']:
                status = child.getText().encode('utf8')
                if status == 'Z-zapis':
                    student_enrolled = True

        if student.surname != '' and student.names != '' and student.number != '' and student_enrolled:
            students.append(student)

    return students


def get_lecture_name(html):

    bs = BeautifulSoup(html, "lxml")
    inp = bs.find("input", {'name':'P_ID_PRZEDMIOTU'})
    ret = inp.attrs['value']

    return ret


def main():

    classes_urls = get_urls()

    students = []
    students_numbers = set()

    lectures = []

    for class_url in classes_urls:

        if class_url is None:
            continue

        lectures_urls = get_lectures_urls(class_url)

        print("Processing class url: {}\n".format(class_url))

        for index, lecture_url in enumerate(lectures_urls):

            lecture = Lecture()

            html = get_content(lecture_url)

            lecture.name = get_lecture_name(html)
            lecture.students = get_lecture_students(html)

            for student in lecture.students:

                if student.number not in students_numbers:
                    students_numbers.add(student.number)
                    students.append(student)

            lectures.append(lecture)

            percent = 100 * index / float(len(lectures_urls))
            print '{:.2f}% \t {}'.format(percent, lecture.name)

    for lecture in lectures:
        for lecture_student in lecture.students:
            for index, student in enumerate(students):

                if lecture_student.number == student.number:
                    student.lectures.append(lecture.name)

    result = Result()
    result.students = students
    result.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print('\n')

    file_students = 'students.json'
    if os.path.isfile(file_students):
        file_students_old = 'students_' + datetime.now().strftime('%Y%m%d_%H%M') + '.json'
        print('Renaming old file with result "{}" to "{}"'.format(file_students, file_students_old))
        os.rename(file_students, file_students_old)

    print('Saving result to file "{}"'.format(file_students))
    output = open(file_students, 'w+')
    output.write(jsonpickle.encode(result, unpicklable=False))
    output.close()
    print('File "{}" saved\n'.format(file_students))

    file_lectures = 'lectures.json'
    if os.path.isfile(file_lectures):
        file_lectures_old = 'lectures_' + datetime.now().strftime('%Y%m%d_%H%M') + '.json'
        print('Renaming old file with result "{}" to "{}"'.format(file_lectures, file_lectures_old))
        os.rename(file_lectures, file_lectures_old)

    print('Saving result to file "{}"'.format(file_lectures))
    output = open(file_lectures, 'w+')
    output.write(jsonpickle.encode(lectures, unpicklable=False))
    output.close()
    print('File "{}" saved'.format(file_lectures))


main()
