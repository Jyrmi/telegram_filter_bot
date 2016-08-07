# This is a simple script for a Instagram-like bot
> **Purpose**
> - To take in an uploaded photo, apply desired filters, and spit back out the processed image
> - Eventually to also have an email component to it so that all processed images are sent via email to the end user

> **Scope**
> - Currently only Telegram
> - Perhaps also Slack and Facebook Messenger and Kakao Talk in the future as well

### Some general tips for getting the bot to work
> - make sure to ping the Telegram API server manually (i.e. visit blablabla/set_webhook)
> - if you get a response from webhook, but it is 500, try some try:...except Exception as e: statements (because heroku's error logs are not very helpful automatically)
> - if still doesn't work, try creating a new heroku app, or even creating a totally new bot (with new bot api key) and see if that worksg
