from transliterate import translit

from django.db import models

from analysis.models import Analys, City, AnalysInBranch


class Question(models.Model):
    name = models.CharField(max_length=127)
    telephone = models.CharField(max_length=63)

    def __str__(self):
        return self.telephone

    def add_question_by_post(post):
        question = Question()

        fields = ['name', 'telephone']

        for field in fields:
            setattr(question, field, post.get(field))

        return question

    def get_html(self):
        return f"""
Вас попросили перезвонить.

Имя: {self.name}
Телефон: {self.telephone}
        """


class Interview(models.Model):
    SEX = (
        ('male', 'Мужчина'),
        ('female', 'Женщина')
    )

    sex = models.CharField(max_length=6, choices=SEX)
    age = models.IntegerField()
    active_rate = models.IntegerField()
    weight = models.IntegerField()
    height = models.IntegerField()
    email = models.EmailField()

    def __str__(self):
        return self.email

    def add_by_post(post):
        interview = Interview()

        fields = ['sex', 'age', 'active_rate', 'weight', 'height', 'email']

        for field in fields:
            setattr(interview, field, post.get(field))

        return interview

    def generate_answer(self):
        interview_answer = InterviewAnswer.find_by_sex_and_age(self.sex, self.age)

        return f"""
<p>Добрый день!</p>

<p>Ваши рекомендации по здоровью:</p>

<p>{self.bmi_answer()}</p>

<p>Важные анализы для вас:</p>

{interview_answer.analysis_answer()}

<p>Узнайте, где можно сдать анализы: <a href="{interview_answer.analysis_url()}">ссылка</a></p>

<p>Врачи, которых нужно посетить:</p>

{interview_answer.doctors_answer()}
        """


    def bmi_answer(self):
        bmi = round(float(self.weight) / (float(self.height) / 100) ** 2)

        if bmi < 18.5:
            result =  "Недостаток веса"
        elif 18.5 <= bmi <= 25:
            result = "Ваш вес в норме"
        elif 25 < bmi <= 30:
            result = "Избыточный вес"
        elif bmi > 30:
            result = "Лишний вес"

        return f"Ваш индекс массы тела - {bmi}. {result}"

    def get_html(self):
        return f"""
Пол: {dict(self.SEX)[self.sex]}
Возраст: {self.age}
Активность: {self.active_rate}
Вес: {self.weight}
Рост: {self.height}
Почта: {self.email}
        """


class InterviewAnalys(models.Model):
    code = models.CharField(max_length=128)
    description = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.code}"


class InterviewDoctor(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=128)

    def __str__(self):
        return f"{translit(self.name, 'ru', reversed=True)}"


class InterviewAnswer(models.Model):
    SEX = (
        ('male', 'Мужчина'),
        ('female', 'Женщина')
    )

    sex = models.CharField(max_length=6, choices=SEX)
    min_age = models.IntegerField()
    max_age = models.IntegerField()

    analysis = models.ManyToManyField(InterviewAnalys)
    doctors = models.ManyToManyField(InterviewDoctor)

    def __str__(self):
        return self.sex + f" {self.min_age}-{self.max_age}"

    def find_by_sex_and_age(sex, age):
        for interview_answer in InterviewAnswer.objects.all():
            if interview_answer.sex == sex and interview_answer.min_age <= int(age) <= interview_answer.max_age:
                return interview_answer

    def analysis_url(self):
        url = 'https://lotoslab.ru/fill_cart_by_url?products='
        products = [a.id for a in self.analysis_obj()]

        return url + str(products)

    def analysis_obj(self):
        analysis = []

        for analys in self.analysis.all():
            a = Analys.objects.filter(code=analys.code).first()

            if not a is None:
                analysis.append(a)

        return analysis

    def analysis_answer(self):
        answer = ""

        for analys_code_desc in self.analysis.all():
            analys = Analys.objects.filter(code=analys_code_desc.code).first()

            if not analys is None:
                answer += f"<p>{analys.name} - {analys_code_desc.description}</p>"

        return answer

    def doctors_answer(self):
        answer = ""

        for doctor in self.doctors.all():
            answer += f"<p>{doctor.name} - {doctor.description}</p>"

        return answer


class Partner(models.Model):
    name = models.CharField(max_length=64)
    specialization = models.CharField(max_length=77)
    specialization_en = models.CharField(max_length=77, default="")
    name_en = models.CharField(max_length=64, default="")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name_en

    @property
    def image(self):
        filename = self.translit(self.name)

        return f'/partners/{filename}.jpeg'

    def translit(self, name):
        return translit(name, 'ru', reversed=True).replace("'",'').replace(' ', '-').lower()

    def get_partner_by_spec_name(spec, name):
        partner = Partner.objects.filter(specialization_en=spec, name_en=name).first()

        return partner

    def get_specialization():
        specializations = set([p.specialization for p in Partner.objects.all()])

        return sorted(list(specializations))

    def get_partner_by_name(doctor_name):
        partner = Partner.objects.filter(name=doctor_name).first()

        if partner is None:
            return Partner(name=doctor_name)

        return partner


class PartnerPackage(models.Model):
    name = models.CharField(max_length=32)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    analysis = models.ManyToManyField(Analys)

    def __str__(self):
        return f"{self.partner} {translit(self.name, 'ru', reversed=True)}"

    def get_package_by_nam_and_partner(package_name, partner):
        package = PartnerPackage.objects.filter(name=package_name, partner=partner).first()

        if package is None:
            return PartnerPackage(name=package_name)

        return package

    def get_analysis(self):
        analysis = {}
        matcheds = set()

        for analys in self.analysis.all():
            matched_id = analys.matched_id
            if matched_id == -1 or not matched_id in matcheds:
                if not analys.section in analysis:
                    analysis[analys.section.capitalize()] = analys.name
                else:
                    analysis[analys.section.capitalize()] += '; ' + analys.name

            matcheds.add(analys.matched_id)

        return analysis

    def get_labaratories(self):
        labs = list(set([analys.labaratory for analys in self.analysis.all()]))
        city = City.get_city_by_name('sankt-peterburg')

        d = {}

        for lab in labs:
            price = 0
            products = []

            for analys in self.analysis.all():
                analys_branch = AnalysInBranch.objects.filter(labaratory_branch__city=city, labaratory_branch__labaratory=lab, analys=analys).first()

                if not analys_branch is None:
                    price += analys_branch.price
                    products.append(analys_branch.analys.id)

            url = '/fill_cart_by_url?products=' + str(products)

            d[lab.name] = (price, url)

        return d

    def get_url(self):
        url = '/fill_cart_by_url?products='
        products = [analys.id for analys in self.analysis.all()]

        return url + str(products)
