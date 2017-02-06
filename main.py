#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import csv
import json
import StringIO
import webapp2

from google.appengine.ext import ndb

def csv_string_to_dict(csv_data):
    precinct_to_votes = {}
    is_header = True
    f = StringIO.StringIO(csv_data)
    rows = csv.reader(f, delimiter=',')
    for row in rows:
        if is_header:
          is_header = False
          continue
        office = row[2]
        if office != 'President':
          continue
        county = row[0]
        precinct = row[1]
        key = county + '__' + precinct
        entry = precinct_to_votes.get(key, {})
        precinct_to_votes[key] = entry
        entry['county'] = county
        entry['precinct'] = precinct

        precinct_votes = entry.get('votes', {})
        entry['votes'] = precinct_votes

        candidate = row[5]
        votes = int(row[6])
        if candidate in precinct_votes:
          precinct_votes[candidate] += votes
        else:
          precinct_votes[candidate] = votes
    return precinct_to_votes

class PrecinctVotes(ndb.Model):
    precinct = ndb.StringProperty()
    county = ndb.StringProperty()
    votes = ndb.JsonProperty()

class UploadHandler(webapp2.RequestHandler):
    def post(self):
        csv_data = self.request.POST.get('csv_file').file.read()
        precinct_to_votes = csv_string_to_dict(csv_data)
        for key in precinct_to_votes:
            entry = precinct_to_votes[key]
            precinct_id = entry['county'] + '__' + entry['precinct']
            new_precinct = PrecinctVotes(
                id = precinct_id,
                county = entry["county"],
                precinct = entry["precinct"],
                votes = entry["votes"]
            )
            new_precinct.put()
        self.response.out.write('Upload successful')

class PrecinctHandler(webapp2.RequestHandler):
    def get(self):
        results = []
        for precinct in PrecinctVotes.query():
            results.append(precinct.to_dict())
        self.response.out.write(json.dumps(results))
        self.response.headers.add_header('Content-Type', 'application/json')

app = webapp2.WSGIApplication([
    ('/upload', UploadHandler),
    ('/precincts', PrecinctHandler)
], debug=True)
