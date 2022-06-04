#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from unicodedata import name
from urllib import response
import dateutil.parser
import babel
from flask import (Flask, jsonify,
                   render_template,
                   request, Response,
                   flash,
                   redirect,
                   url_for)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import (db,
                    Artist,
                    Venue,
                    Show)
import os
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)

#----------------------------------------------------------------------------#
# Model
#----------------------------------------------------------------------------#

app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#------------------------------------------------------------------#
#  Search
#------------------------------------------------------------------#

def search(table, return_value):
    response = ""
    if return_value != "":
        try:
            results = table.query.filter(table.name.ilike(
                "%" + return_value + "%")).order_by("id").all()
            print(results)
            if len(results) == 0:
                flash(f'{return_value} has no matching records')
            response = {
                "count": len(results),
                "data": [{
                    "id": result.id,
                    "name": result.name,
                    "num_of_upcoming_shows": Show.query.filter_by(venue_id=result.id).count()
                } for result in results]
            }
        except Exception as error:
            flash(f'{error}')
    else:
        response = {
            "count": 0, "data": [{}]
        }
        flash(f'Please enter a valid word')
    return response

#------------------------------------------------------------------#
#  Venues
#  ----------------------------------------------------------------#


@app.route('/venues')
def venues():

    data = []
    venues = Venue.query.all()
    locations = set([loc.city for loc in venues])

    for city in locations:
        locations_venue = Venue.query.filter_by(
            city=city).order_by('name').all()
        data.append({
            "city": locations_venue[0].city,
            "state": locations_venue[0].state,
            "venues": [{
                    "id": location.id,
                    "name": location.name,
                    "num_upcoming_shows": Show.query.filter_by(venue_id=location.id).count()
                    } for location in locations_venue]
        })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    return_value = request.form.get("search_term", "")
    response = search(Venue, return_value)

    return render_template('pages/search_venues.html', results=response, search_term=return_value)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    past_shows = db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()
    upcoming_shows = db.session.query(Show).join(Venue).filter(
        Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()

    venue.past_shows = past_shows
    venue.upcoming_shows = upcoming_shows

    venue.past_shows_count = len(past_shows)
    venue.upcoming_shows_count = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=venue)


#------------------------------------------------------------------#
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    if form.validate_on_submit():
        try:
            create_venue = Venue(name=request.form.get('name'),
                                 city=request.form.get('city'), state=request.form.get('state'),
                                 genres=request.form.get('genres'),
                                 address=request.form.get('address'),
                                 phone=request.form.get('phone'),
                                 image_link=request.form.get('image_link'),
                                 facebook_link=request.form.get(
                                     'facebook_link'),
                                 website=request.form.get('website_link'),
                                 seeking_talent=request.form.get(
                'seeking_talent') == 'y',
                seeking_description=request.form.get('seeking_description'))
            db.session.add(create_venue)
            db.session.commit()
            flash(f'Venue {request.form["name"]} was successfully listed!')
        except Exception as error:
            flash(f'{error} Venue {request.form["name"]} could not be listed')
        finally:
            db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    delete_item = Venue.query.get(venue_id)

    if delete_item is None:
        return os.abort(400)
    try:
        db.session.delete(delete_item)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    return jsonify({
        "message": "Delete Successful!"})


#------------------------------------------------------------------#
#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():

    artists = Artist.query.order_by('name').all()
    data = [{
        "id": artist.id,
        "name": artist.name
    } for artist in artists]

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():

    return_value = request.form.get("search_term", "")
    response = search(Artist, return_value)

    return render_template('pages/search_artists.html', results=response, search_term=return_value)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    past_shows = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()
    upcoming_shows = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()

    artist.past_shows = past_shows
    artist.upcoming_shows = upcoming_shows

    artist.past_shows_count = len(past_shows)
    artist.upcoming_shows_count = len(upcoming_shows)
    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm()
    if form.validate_on_submit():
        try:
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.genres = form.genres.data
            artist.phone = form.phone.data
            artist.image_link = form.image_link.data
            artist.facebook_link = form.facebook_link.data
            artist.website = form.website_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data

            db.session.commit()
            flash(
                f'Artist {request.form["name"]} has been successfully updated!')
        except Exception as error:
            db.session.rollback()
            flash(
                f'{error} Artist {request.form["name"]} was unsuccessfully updated')
        finally:
            db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm()
    if form.validate_on_submit():
        try:
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.genres = form.genres.data
            venue.phone = form.phone.data
            venue.image_link = form.image_link.data
            venue.facebook_link = form.facebook_link.data
            venue.website = form.website_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data

            db.session.commit()
            flash(
                f'Venue {request.form["name"]} has been successfully updated!')
        except Exception as error:
            db.session.rollback()
            flash(
                f'{error} Venue {request.form["name"]} was unsuccessfully updated')
        finally:
            db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#------------------------------------------------------------------#
#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    if form.validate_on_submit():
        try:
            create_artist = Artist(name=request.form.get('name'),
                                   city=request.form.get('city'), state=request.form.get('state'),
                                   genres=request.form.get('genres'),
                                   phone=request.form.get('phone'),
                                   image_link=request.form.get('image_link'),
                                   facebook_link=request.form.get(
                                       'facebook_link'),
                                   website=request.form.get('website_link'),
                                   seeking_venue=request.form.get(
                'seeking_venue') == 'y',
                seeking_description=request.form.get('seeking_description'))
            db.session.add(create_artist)
            db.session.commit()
            flash(f'Artist {request.form["name"]} was successfully listed!')
        except Exception as error:
            flash(f'{error} Artist {request.form["name"]} could not be listed')
        finally:
            db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    shows = Show.query.all()
    for show in shows:
        show_venue = Venue.query.get(show.venue_id)
        show_artist = Artist.query.get(show.artist_id)

        data.append({
            "id": show.id,
            "artist_id": show_artist.id,
            "artist_name": show_artist.name,
            "artist_image_link": show_artist.image_link,
            "venue_id": show_venue.id,
            "venue_name": show_venue.name,
            "start_time": show.start_time
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()
    if form.validate_on_submit():
        try:
            create_shows = Show(artist_id=request.form.get('artist_id'),
                                venue_id=request.form.get('venue_id'),
                                start_time=request.form.get('start_time'))
            db.session.add(create_shows)
            db.session.commit()
            flash('Show was successfully listed!')
        except:
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()

    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
