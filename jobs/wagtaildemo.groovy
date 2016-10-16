// WAGTAIL_SSH_USER and WAGTAIL_HOST should be provided by the seed job's environment

String fabric_script(String command, String args = "") {
    return """
    # Assumptions:
    # - virtualenv is installed on the jenkins host (apt-get install python-virtualenv)
    # - jenkins can SSH into \$USER@\$HOST using a passwordless SSH key

    USER="${WAGTAIL_SSH_USER}"
    HOST="${WAGTAIL_HOST}"

    virtualenv venv
    source venv/bin/activate
    pip install fabric
    fab $command -u \$USER -H \$HOST $args
   """.stripIndent()
}

job('Initialize Wagtail Webserver') {
    scm {
        git {
		    remote {
			    url ('https://github.com/m3brown/wagtail-bootstrap')
            }
		}
	}
    steps {
        shell(fabric_script(command="init"))
    }
}

job('Deploy Wagtail') {
    scm {
        git {
		    remote {
			    url ('https://github.com/m3brown/wagtail-bootstrap')
            }
		}
	}
    steps {
        shell(fabric_script(command="deploy"))
    }
}
