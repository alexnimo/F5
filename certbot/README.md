<h1> <a target="_blank" href="https://certbot.eff.org/">
<img src="https://certbot.eff.org/images/certbot-logo-1A.svg" alt="certbot bot" width="200px" height="200px" align="left"></a>
F5 Certbot Automator
</h1>
<h2> Abstract </h2>
<p>
This project uses lukas2511's <a target="_blank" href="https://github.com/lukas2511/dehydrated"> dehydrated </a> script
as a base to deploying letsencrypt certificate automatically to the F5 Big-IP.

I'm not a codder and therefore my hook script is a dirty python script, not code efficient and probably poorly written but in the process of writing the script I've learned a bit about many different topics like: python, F5 api and SDK, docker, automation, certbot and much more.

The main purpose of this hook script is to configure every aspect of the Big-IP automatically.
The challenge that is being implemented is http, to my opinion it's more generic then DNS.
</p>

<h2>Usage</h2>
<h3>Configuration</h3>
<p> dehydrated configuration can be changed by editing the config file( you can also run the script with the default config file). &nbsp;
Some basic configuration must be made in the certbot_hook.py:
</p>
<code>
BIGIP_MNG_IP = "" - The management IP address of the Big-IP &nbsp;
BIGIP_CERTBOT_VERIFICATION_VS_IP = "" - The IP address of the VS which will be used for the verification challenge ( Can be the same as the actual SSL VS ) &nbsp;
BIGIP_SSL_VS_IP = "" - The IP of the actual VS server that will be used in production
</code>

<h3>Simple bash command</h3>
This simple command with your actual domain will deploy the challenge, generate an appropriate certificate, upload it to the Big-IP and will create the SSL client profile and VS. &nbsp;
<code> ./dehydrated --accept-terms -c -d www.mydomain.net -k /certbot/dehydrated/certbot_hook.py
</code>
<h3>Docker</h3>
<h2>Contributors</h2>

<p> Most of this project is based on an amazing work the following projects: </p>

<ul>
<li>Without it( and lets-encrypt ), non of these were possible - <a target="_blank" href="https://github.com/lukas2511/dehydrated"></li>
<li>Some of the code is directly taken form the hook script of f5 - <a target="_blank" href="https://github.com/f5devcentral/lets-encrypt-python"> </li>
<li>Lots of help from F5 Dev Central - <a target="_blank" href="https://devcentral.f5.com"></li>
<li>Lots of time spent with the API docs: - <a target="_blank" href="http://f5-sdk.readthedocs.io"></li>
</ul>
<h2>To-Do List<h2>
<li>Configure ssl profile with strong ciphers</li>
<li>Assign HTTP profile with HSTS </li>
<li>integration with additional modules and vendors</li>
<li>Slack updates / Integration </li>
<li>Delete Old certs and keys in cert directory (script mode / Docker with attached storage)</li>
<li>Check certificate expiration date(python/shell script) before executing dehydrated (script mode + ephemeral docker container) </li>
