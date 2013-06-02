# Stopgap

The voting system that had to be done.

## Requirements

- MongoDB
- sendmail
- Python 3.2 or higher
  - Modules:
    - pymongo
    - tornado
    - bbqutils

It is recommended that you put this system behind nginx or another HTTP daemon.

## Installation

Recommended operating system is Ubuntu LTS 12.04, and the installation instructions assume Ubuntu 12.04.

### Dependencies

```
$ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
$ echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/10gen.list
$ sudo apt-get update
$ sudo apt-get install sendmail mongodb-10gen python3 python3-dev python3-setuptools build-essential
$ sudo easy_install3 virtualenv
$ virtualenv py32
$ source py32/bin/activate
$ pip install pymongo tornado bbqutils
```

### Running Stopgap

```
$ git clone https://github.com/bbqsrc/stopgap.git
$ source py32/bin/activate
$ cd stopgap
$ python server.py --port=<port>
```

Ensure you have reverse DNS set up correctly and SPF records set on your DNS for the domain to ensure delivery of the token emails.

## Usage

In essense, this system is merely a server that uses single-use tokens to take an HTTP POST of data from an end user for later processing as part of an election algorithm, for surveys, etc.

This system has two concepts: elections and ballots.

An election consists of the ballot page, a successful ballot receipt page and an error page, with a user list that will be mailed unique keys for interacting with this election. The election has a start and end time, and you may add further users to the list and mail out keys to those users in the event that a user is missed.

A ballot is the user response to the election and is stored with a unique ID and linked to the election ID.

### Creating an election

#### Consider your slug

The slug is the identifier for your election such as `my-election-2013`.

#### Create the ballot

Create a HTML form for your ballots. It may take any form, as long as the final result is the user POSTing data to the same slug as was selected for the election.

Dump any necessary dependencies (such as jQuery) into the static directory.

As the output is JSON, the notation for the HTML form input fields is in a JSON-style notation. In order to create a structure like this:

```json
{
  "candidates": {
    "A": 1,
    "B": 2,
    "C": 3
  }
}
```

One might make an HTML form such as:

```html
<form method="post">
  <input name="candidates[A]">
  <input name="candidates[B]">
  <input name="candidates[C]">
</form>
```

The backend will autogenerate missing parents, so `<input name='foo[bar][baz]'>` would be valid as well.

#### Prepare your user list and email

- The user list should consist of just email addresses each on their own line.
- You will need to create an email template that will be used to inform users of their unique voting token.
  - Your template must include a url that includes `/{slug}/{token}` such as `http://vote.tld/{slug}/{token}`

#### Start the election

*Currently the `startTime` property is set the moment you create the election, but nobody may vote until you send them their unique token*

We create an election using the `create.py` script. For example:

```
$ python create.py my-special-election users.txt ballot.html success.html error.html email.txt "Voting System <foo@bar.tld>" "Voting System Ballot: PLEASE VOTE!"
```

Once you are prepared to mail out the tokens to the users, use the `send.py` script. You may opt to do a dry run using `-d`, and running this script will ask you to confirm that you wish to send the tokens out to the recipients before starting.

If you miss any users (it happens), you can add them at any time using the `add_email.py` script and running `send.py` again. `send.py` will not send the same token twice, as recipients are flagged as having had their token sent.

Note: _Tokens are not linked to email addresses and therefore cannot be linked back to the email address._

### Finishing an election

#### End the election

The easiest way to end an election currently is to run the `end.py` script with the `slug` as the first parameter for the election you want to end. Use the `at` application to set a specific time for ending the election if you need precise timing.

#### Exporting the ballots and elections

For verifiability purposes, it is a good idea to export both the elections and the ballots and publish them for those who wish to scrutinise the process. The `export_elections.py` script will export your chosen election, stripping any personally identifying information such as email addresses, while keeping the tokens intact.

The `export_ballots.py` script will export all the ballots for the chosen slug in JSON format for processing by another system.

## License

Creative Commons Zero - do what you want.
