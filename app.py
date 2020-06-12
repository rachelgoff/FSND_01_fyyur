#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

default_artist_image_link = 'https://images.unsplash.com/photo-1569437061238-3cf61084f487?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=634&q=80'
default_venue_image_link = 'https://assets.entrepreneur.com/content/3x2/2000/20190705133921-shutterstock-208432186.jpeg?width=700&crop=2:1'

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.String(120))
    shows = db.relationship("Show", backref=db.backref('venue', lazy=True))

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    venue_image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref=db.backref('artist', lazy=True))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

# Display a list of venues
@app.route('/venues')
def venues():
  data = []
  venue_cities = {}
  error = False
  try:
    venues = Venue.query.with_entities(Venue.id, Venue.name, Venue.city, Venue.state).all()

    # Get a list of cities per city and state and group the venues
    for venue in venues:
      city_state = venue.city + ',' + venue.state
      if not city_state in venue_cities:
        venue_cities[city_state]=[]
      venue_cities[city_state].append(venue)

    # Format city, state and venues value in a way that is served as data
    for key in venue_cities.keys():
      city_state = key.split(',')
      city_venue= {
        "city":city_state[0],
        "state":city_state[1],
        "venues":venue_cities[key]
      }
      data.append(city_venue)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else:  
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  data = []
  error = False
  try:
    # Implement search on venues with partial string search. Ensure it is case-insensitive.
    search_term = request.form.get('search_term')
    search_results = Venue.query.filter(Venue.name.ilike("%" + search_term + "%"))
    num_results = search_results.count()
    for result in search_results:
        data_item = {
        "id": result.id,
        "name": result.name,
        }
        data.append(data_item)

    response = {
      "count": num_results,
      "data": data
    }
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else: 
    return render_template('pages/search_venues.html', results=response, search_term=search_term)

# Display the sepicified venue page
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  upcoming_shows_count = 0
  past_shows_count = 0
  upcoming_shows = []
  past_shows = []
  data = {}
  error = False
  try:
    venue = Venue.query.get(venue_id)
    shows = venue.shows
    for show in shows:
      # upcoming shows
      if show.start_time > datetime.utcnow(): 
        upcoming_shows_count += 1
        artist = show.artist
        upcoming_shows_item = {
          "artist_id": artist.id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link or default_artist_image_link,
          "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        upcoming_shows.append(upcoming_shows_item)
      else:
        # caculate past shows
        past_shows_count += 1
        artist = show.artist
        past_shows_item = {
          "artist_id": artist.id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link or default_artist_image_link,
          "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        past_shows.append(past_shows_item)

  # need to format the genres valune obtained from DB into a list of genres
    genres_list = []
    new_genres = venue.genres[1:-1].split(",")
    for genre in new_genres:
        genres_list.append(genre)

    data = {
      "id": venue_id,
      "name": venue.name,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "address": venue.address,
      "genres": genres_list,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link or default_venue_image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": past_shows_count,
      "upcoming_shows_count": upcoming_shows_count
    }
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else: 
    return render_template('pages/show_venue.html', venue=data)
 
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    name = request.form.get('name', '')
    city = request.form.get('city','')
    state = request.form.get('state','')
    address = request.form.get('address','')
    phone = request.form.get('phone','')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link','')
    image_link = request.form.get('image_link','')
    seeking_talent = request.form.get('seeking_talent', '')
    website = request.form.get('website', '')
    seeking_description = request.form.get('seeking_description', '')

    if seeking_talent == 'True':
      seeking_talent = True
    else:
      seeking_talent = False

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, website=website, facebook_link=facebook_link, image_link=image_link, seeking_description=seeking_description, seeking_talent=seeking_talent)
    db.session.add(venue)
    db.session.commit()
    venue_id = venue.id
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form.get('name') + ' could not be listed.')
    return abort(400)
  else:    
    flash('Venue ' + request.form.get('name') + ' was successfully listed!')
    return redirect('/venues/' + str(venue_id))

# Delete a specific venue entry
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue_shows = Show.query.filter_by(venue_id=venue_id).all()
    for show in venue_shows:
      db.session.delete(show)
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect('/')

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    name = request.form.get('name', '')
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    phone = request.form.get('phone', '')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link', '')
    image_link = request.form.get('image_link', '')
    website = request.form.get('website', '')
    venue_image_link = request.form.get('venue_image_link', '')
    seeking_venue = request.form.get('seeking_venue', '')
    seeking_description = request.form.get('seeking_description', '')

    if seeking_venue == 'True':
      seeking_venue = True
    else:
      seeking_venue = False

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website,venue_image_link=venue_image_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
    artist_id = artist.id
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    return abort(400)
  else: 
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return redirect('/artists/' + str(artist_id))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

#Implement search on artists with partial string search.
@app.route('/artists/search', methods=['POST'])
def search_artists():
  data = []
  error = False
  try:
    search_term = request.form.get('search_term')
    search_results = Artist.query.filter(Artist.name.ilike("%" + search_term + "%"))
    num_results = search_results.count()
    for result in search_results:     
        data_item = {
        "id": result.id,
        "name": result.name,
        }
        data.append(data_item)

    response = {
      "count": num_results,
      "data": data
    }
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else: 
    return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  upcoming_shows_count = 0
  past_shows_count = 0
  upcoming_shows = []
  past_shows = []
  data = {}
  error = False
  try:
    artist = Artist.query.get(artist_id)
    shows = artist.shows
    for show in shows:
      if show.start_time > datetime.utcnow():
        # upcoming shows on artist page
        upcoming_shows_count += 1
        venues = Venue.query.filter_by(id=show.venue_id).all()
        for venue in venues:
          upcoming_shows_item = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": artist.venue_image_link or default_venue_image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
          }
          upcoming_shows.append(upcoming_shows_item)
      else:
        # past shows on artist page
        past_shows_count += 1
        venues = Venue.query.filter_by(id=show.venue_id).all()
        for venue in venues:
          past_shows_item = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "venue_image_link": artist.venue_image_link or default_venue_image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
          }
          past_shows.append(past_shows_item)
    
    if artist.seeking_venue == 'True':
      artist.seeking_venue = True
    elif artist.seeking_venue == 'False':
      artist.seeking_venue = False
    
    genres_list = []
    new_genres = artist.genres[1:-1].split(",")
    for genre in new_genres:
        genres_list.append(genre)

    data = {
      "id": artist_id,
      "name": artist.name,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "genres": genres_list,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link or default_artist_image_link,
      "facebook_link": artist.facebook_link,
      "venue_image_link": artist.venue_image_link or default_venue_image_link,
      "website": artist.website,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": past_shows_count,
      "upcoming_shows_count": upcoming_shows_count
    }
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else: 
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
# edit artist page
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  error = False
  try:
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    if artist.seeking_venue == True:
      artist.seeking_venue = 'True'
    else:
      artist.seeking_venue = 'False'

    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.website.data = artist.website
    form.facebook_link.data = artist.facebook_link
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else: 
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False

  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form.get('name', '')
    artist.city = request.form.get('city', '')
    artist.state = request.form.get('state', '')
    artist.phone = request.form.get('phone', '')
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form.get('facebook_link', '')
    artist.image_link = request.form.get('image_link', '')
    artist.website = request.form.get('website', '')
    artist.venue_image_link = request.form.get('venue_image_link', '')
    artist.seeking_venue = request.form.get('seeking_venue', '')
    artist.seeking_description = request.form.get('seeking_description', '')

    if artist.seeking_venue == 'True':
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False

    artist = Artist(name=artist.name, city=artist.city, state=artist.state, phone=artist.phone, genres=artist.genres, facebook_link=artist.facebook_link, image_link=artist.image_link, website=artist.website,venue_image_link=artist.venue_image_link, seeking_venue=artist.seeking_venue, seeking_description=artist.seeking_description)
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    return abort(400)

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  error = False
  try:
    form = VenueForm()
    # populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)

    if venue.seeking_talent == True:
      venue.seeking_talent = 'True'
    else:
      venue.seeking_talent = 'False'

    form.name.data = venue.name
    form.genres.data = venue.genres
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else: 
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # update existing venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  error = False
  try:
    venue.name = request.form.get('name', '')
    venue.city = request.form.get('city','')
    venue.state = request.form.get('state','')
    venue.address = request.form.get('address','')
    venue.phone = request.form.get('phone','')
    venue.genres = request.form.getlist('genres')
    venue.facebook_link =request.form.get('facebook_link','')
    venue.image_link =request.form.get('image_link','')
    venue.website =request.form.get('website','')
    venue.seeking_talent = request.form.get('seeking_talent', '')
    venue.seeking_description = request.form.get('seeking_description', '')

    if venue.seeking_talent == 'True':
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False

    venue = Venue(name=venue.name, city=venue.city, state=venue.state, address=venue.address, phone=venue.phone, genres=venue.genres, facebook_link=venue.facebook_link, image_link=venue.image_link, website=venue.website, seeking_talent=venue.seeking_talent, seeking_description=venue.seeking_description)
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else:    
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Shows
#  ----------------------------------------------------------------
# Display a list of shows
@app.route('/shows')
def shows():
  show_list = []
  error = False
  try:
    shows = Show.query.all()
    for show in shows:
      venue = show.venue
      artist = show.artist
      show_item = {
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link or default_artist_image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
      show_list.append(show_item)
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else: 
    return render_template('pages/shows.html', shows=show_list)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form.get('artist_id', '')
    venue_id = request.form.get('venue_id', '')
    start_time = request.form.get('start_time', '')
    new_show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    
    db.session.add(new_show)
    db.session.commit()
  # Get new show id after commiting to DB
    new_show_id = new_show.id
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not tbe listed.')
    return abort(400)
  else:
    flash('Show was successfully listed!')
    return redirect('/shows/' + str(new_show_id))

@app.route('/shows/<int:show_id>')
def show_showitem(show_id):
  error = False
  try:
    show = Show.query.get(show_id)
    venue = show.venue
    artist = show.artist
    data = [{
      "id": show.id,
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link or default_artist_image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    }]
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
      db.session.close()
  if error:
    return abort(400)
  else: 
    return render_template('pages/shows.html', shows=data)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
