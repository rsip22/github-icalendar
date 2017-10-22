
"""
#!/usr/bin/env python
.. module:: main
   :synopsis: Render Github issues as iCalendar feed
.. moduleauthor:: Daniel Pocock http://danielpocock.com

"""

# Copyright (C) 2015, Daniel Pocock http://danielpocock.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import github
import yaml
import icalendar
import logging
import os


log = logging.getLogger(__name__)


def setup_logging():
    log.setLevel(logging.DEBUG)
    console_out = logging.StreamHandler()
    console_out.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console_out.setFormatter(formatter)
    log.addHandler(console_out)
    # github.enable_console_debug_logging()


def display(cal):
    return cal.to_ical().replace('\r\n', '\n').strip()


def make_uid(issue):
    return "%s-%s.issue.github.com" % (issue.number, issue.id)


def make_title(repo_title, issue):
    return "%s #%s: %s" % (repo_title, issue.number, issue.title)


def make_reporter(issue):
    return "%s@users.github.com" % issue.user.login


def make_labels(issue):
    return [item.name for item in issue.labels]


# when the issue has a given label, set an iCalendar category for the issue
# not implemented yet
def set_category(todo, label, category=None):
    if label in todo['labels']:
        todo.add('category', category)


# when the issue has a given label, set an iCalendar status for the issue
# not implemented yet
def set_status(todo, label, status):
    if label in todo['labels']:
        todo.add('status', status)


def make_todo(issue, repo_title=None):
    if repo_title is None:
        repo_title = issue.repository.name
    try:
        todo = icalendar.Todo()
        todo['uid'] = make_uid(issue)
        todo['summary'] = make_title(repo_title, issue)
        todo['description'] = issue.body
        todo['url'] = issue.html_url
        todo['created'] = issue.created_at
        todo['last-modified'] = issue.updated_at
        todo['status'] = 'NEEDS-ACTION'
        todo['organizer'] = make_reporter(issue)
        todo['labels'] = make_labels(issue)
        return todo

    except Exception:
        log.error("Failed to parse %r", t, exc_info=True)
        return None


# When the issue has a given label, give the priority specified
# not implemented yet
def prioritize_label(todo, label, priority_value=None):
    for item in todo['labels']:
        if item == label:
            todo.add('priority', priority_value)
    return todo


def fetch_issues_by_label(github_client, label_name, repo_name=None):
    items = []
    if repo_name is not None:
        repos = [github_client.get_repo(repo_name)]
    else:
        repos = github_client.get_user().get_repos()
    for item in repos:
        try:
            label_repo = item.get_label(label_name)
        except github.UnknownObjectException:
            continue
        if item.has_issues:
            for issue in list(item.get_issues(labels=[label_repo])):
                todo = make_todo(issue)
                if todo is None:
                    return None
                items.append(todo)
    log.debug("Found %d items" % len(items))
    return items


def fetch_issues_by_repo(github_client, repo_name):

    repo_name_parts = repo_name.split('/')
    repo_title = repo_name_parts[1]
    repo = github_client.get_repo(repo_name)

    items = []
    for issue in repo.get_issues(state='open'):
        todo = make_todo(issue, repo_title)
        if todo is None:
            return None
        items.append(todo)
    log.debug("Found %d items" % len(items))
    return items


def fetch_issues(github_client, filter):
    items = []
    for issue in github_client.get_user().get_issues(state='open',
                                                     filter=filter):
        todo = make_todo(issue)
        if todo is None:
            return None
        items.append(todo)
    log.debug("Found %d items" % len(items))
    return items


def generate_ical(conf):
    if conf is None:
        raise ValueError("Missing configuration")

    github_client = github.Github(
        conf['api_token'],
        user_agent='Github-iCalendar')
    cal = icalendar.Calendar()
    cal.add('prodid', '-//danielpocock.com//GithubIssueFeed//')
    cal.add('version', '1.0')
    if 'labels' in conf:
        if 'repositories' in conf:
            log.debug("Using configured repository and labels list")
            for repo_details in conf['repositories']:
                repo_name = repo_details['repository']
                log.debug("trying repository: %s" % (repo_name))
                for label_details in conf['labels']:
                    label_name = label_details['label']
                    log.debug("trying labels: %s" % (label_name))
                    items = fetch_issues_by_label(github_client,
                                                  label_name,
                                                  repo_name)
                    if items is None:
                        raise ValueError("Error parsing Github data for %s"
                                         % repo_name)
                    for item in items:
                        cal.add_component(item)
        else:
            log.debug("Using configured labels list")
            for label_details in conf['labels']:
                label_name = label_details['label']
                log.debug("trying labels: %s" % (label_name))
                items = fetch_issues_by_label(github_client, label_name)
                if items is None:
                    raise ValueError("Error parsing Github data for %s"
                                     % label_name)
                for item in items:
                    cal.add_component(item)
    elif 'repositories' in conf:
        log.debug("Using configured repository list")
        for repo_details in conf['repositories']:
            repo_name = repo_details['repository']
            log.debug("trying repository: %s" % (repo_name))
            items = fetch_issues_by_repo(github_client, repo_name)
            if items is None:
                raise ValueError("Error parsing Github data for %s"
                                 % repo_name)
            for item in items:
                cal.add_component(item)
    else:
        log.debug("Fetching issues for all of the repositories and all labels")
        if 'filter' in conf:
            filter = conf['filter']
        else:
            filter = 'all'
        items = fetch_issues(github_client, filter)
        if items is None:
            raise ValueError("Error parsing Github data for %s" % repo_name)

        for item in items:
            cal.add_component(item)
    return "%s" % display(cal)


def run_webapp(conf, debug):
    import flask
    app = flask.Flask(__name__)

    @app.route("/")
    def service():
        try:
            output = generate_ical(conf)
        except ValueError as e:
            return flask.Response(status_code=500, status=str(e))
        else:
            return flask.Response(output, mimetype='text/calendar')
    app.run(host=conf['bind_address'], port=conf['bind_port'], debug=debug)


if __name__ == '__main__':
    setup_logging()
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('config_filename')
    arg_parser.add_argument('--web', action='store_true')
    arg_parser.add_argument('--debug', action='store_true')
    args = arg_parser.parse_args()
    with open(args.config_filename) as f:
        conf = yaml.load(f)
        log.info("Config loaded")
    if args.web:
        run_webapp(conf, args.debug)
    else:
        print(generate_ical(conf))
