# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Companies(models.Model):
    name = models.CharField()
    size = models.SmallIntegerField(blank=True, null=True)
    country_code = models.ForeignKey('Countries', models.DO_NOTHING, db_column='country_code')
    website_url = models.CharField(blank=True, null=True)
    logo_url = models.CharField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'companies'


class Countries(models.Model):
    code = models.CharField(primary_key=True, max_length=2)
    name = models.CharField()
    class Meta:
        managed = False
        db_table = 'countries'


class Currencies(models.Model):
    code = models.CharField(primary_key=True)
    symbol = models.CharField(blank=True, null=True)
    name = models.CharField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'currencies'


class EmploymentTypes(models.Model):
    type = models.CharField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'employment_types'


class EmploymentUnits(models.Model):
    unit = models.CharField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'employment_units'


class ExperienceLevels(models.Model):
    level = models.CharField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'experience_levels'


class JobBoardWebsites(models.Model):
    name = models.CharField(primary_key=True)
    website_url = models.CharField()
    class Meta:
        managed = False
        db_table = 'job_board_websites'


class LanguageLevels(models.Model):
    level = models.CharField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'language_levels'


class Languages(models.Model):
    code = models.CharField(primary_key=True)
    name = models.CharField()
    class Meta:
        managed = False
        db_table = 'languages'


class Locations(models.Model):
    country_code = models.ForeignKey(Countries, models.DO_NOTHING, db_column='country_code')
    city = models.CharField()
    street = models.CharField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=65535, decimal_places=65535)
    longitude = models.DecimalField(max_digits=65535, decimal_places=65535)
    class Meta:
        managed = False
        db_table = 'locations'


class OfferCategories(models.Model):
    name = models.CharField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'offer_categories'


class OfferSalaries(models.Model):
    offer = models.ForeignKey('Offers', models.DO_NOTHING)
    currency = models.ForeignKey(Currencies, models.DO_NOTHING, db_column='currency')
    salary_min = models.IntegerField()
    salary_max = models.IntegerField(blank=True, null=True)
    is_gross = models.BooleanField()
    unit = models.ForeignKey(EmploymentUnits, models.DO_NOTHING, db_column='unit')
    type = models.ForeignKey(EmploymentTypes, models.DO_NOTHING, db_column='type')
    class Meta:
        managed = False
        db_table = 'offer_salaries'


class Offers(models.Model):
    job_board_name = models.ForeignKey(JobBoardWebsites, models.DO_NOTHING, db_column='job_board_name')
    company = models.ForeignKey(Companies, models.DO_NOTHING)
    title = models.CharField()
    description = models.TextField(blank=True, null=True)
    apply_url = models.CharField()
    experience_level = models.ForeignKey(ExperienceLevels, models.DO_NOTHING, db_column='experience_level')
    workplace_type = models.ForeignKey('WorkplaceTypes', models.DO_NOTHING, db_column='workplace_type')
    working_time = models.ForeignKey('WorkingTimes', models.DO_NOTHING, db_column='working_time')
    publish_date = models.DateTimeField()
    expire_date = models.DateTimeField()
    raw_json = models.JSONField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'offers'


class OffersCategories(models.Model):
    pk = models.CompositePrimaryKey('offer_id', 'category_name')
    offer = models.ForeignKey(Offers, models.DO_NOTHING)
    category_name = models.ForeignKey(OfferCategories, models.DO_NOTHING, db_column='category_name')
    class Meta:
        managed = False
        db_table = 'offers_categories'


class OffersLanguages(models.Model):
    pk = models.CompositePrimaryKey('offer_id', 'language_code')
    offer = models.ForeignKey(Offers, models.DO_NOTHING)
    language_code = models.ForeignKey(Languages, models.DO_NOTHING, db_column='language_code')
    language_level = models.ForeignKey(LanguageLevels, models.DO_NOTHING, db_column='language_level', blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'offers_languages'


class OffersLocations(models.Model):
    pk = models.CompositePrimaryKey('offer_id', 'location_id')
    offer = models.ForeignKey(Offers, models.DO_NOTHING)
    location = models.ForeignKey(Locations, models.DO_NOTHING)
    class Meta:
        managed = False
        db_table = 'offers_locations'


class OffersOptionalSkills(models.Model):
    pk = models.CompositePrimaryKey('offer_id', 'skill_name')
    offer = models.ForeignKey(Offers, models.DO_NOTHING)
    skill_name = models.ForeignKey('Skills', models.DO_NOTHING, db_column='skill_name')
    skill_level = models.ForeignKey('SkillLevels', models.DO_NOTHING, db_column='skill_level')
    class Meta:
        managed = False
        db_table = 'offers_optional_skills'


class OffersSkills(models.Model):
    pk = models.CompositePrimaryKey('offer_id', 'skill_name')
    offer = models.ForeignKey(Offers, models.DO_NOTHING)
    skill_name = models.ForeignKey('Skills', models.DO_NOTHING, db_column='skill_name')
    skill_level = models.ForeignKey('SkillLevels', models.DO_NOTHING, db_column='skill_level', blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'offers_skills'


class SkillLevels(models.Model):
    level = models.IntegerField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'skill_levels'


class Skills(models.Model):
    name = models.CharField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'skills'


class WorkingTimes(models.Model):
    type = models.CharField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'working_times'


class WorkplaceTypes(models.Model):
    type = models.CharField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'workplace_types'
