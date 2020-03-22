# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # This is the database box, which is just a postgres database.
  # We define the database first so that it is loaded before the web server.
  config.vm.define "db" do |db|
    db.vm.box = "ubuntu/bionic64"

    # Create a private network, which allows host-only access to the machine using a specific IP.
    db.vm.network "private_network", ip: "10.5.5.11"

    # The database server does not need to be particularly high-spec, so we run it with 1 GB of memory.
    db.vm.provider "virtualbox" do |vb|
      vb.gui = false
      vb.memory = 1024 # 1 GB
    end

    # Install and configure postgres.
    config.vm.provision "shell", inline: <<-SHELL
      # Add the Postgres repository
      echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
      wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

      # Install Postgres
      apt-get update -qq &>/dev/null
      apt-get install -qq -o=Dpkg::Use-Pty=0 postgresql-11 &>/dev/null

      # Configure Postgres
      sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres'"
      sed -i.bak "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/11/main/postgresql.conf
      echo 'host  all  all 0.0.0.0/0 md5' >> /etc/postgresql/11/main/pg_hba.conf
      systemctl restart postgresql.service
    SHELL
  end
end
