# Youtube-download-bot
Telegram bot for Youtube download

## If you use Docker, [recommended]:
# clone the repository
git clone ... 

# update credentials
update scripts/config.ini

# create docker image
docker build -t yt_dl .

# run container
sudo docker run --name yt_dl_container --restart always -d yt_dl


## If you want to run this **locally**, requires: 
1. Creation of a folder called "downloads" in the same directory where the code is executed.
2. An account in mega.nz
3. Update the Mega credentials details in config.ini
4. Update the Telegram token in config.ini
