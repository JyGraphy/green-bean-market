# Fuji PXG4 setup for coffee roasting, step by step guide

- machine: fuji-royal
- source_url: http://kostverlorenvaart.blogspot.com/2014/01/fuji-pxg4-setup-for-coffee-roasting.html
- fetched_at: 2026-08-31
- note: Fuji PXG4 컨트롤러+서모커플 로스팅 셋업 블로그 (세션 WebFetch 403, blogspot 차단)

> 이 파일은 자동 수집된 **원본**이다. 수정하지 않는다.
> 여기서 읽은 내용을 `machines/fuji-royal.md` 의 판독 규칙으로 옮기면 학습이 된다.

---

Fuji PXG4 setup for coffee roasting, step by step guide
Doorgaan naar hoofdcontent
Fuji PXG4 setup for coffee roasting, step by step guide
Link ophalen
Facebook
X
Pinterest
E-mail
Andere apps
-
januari 26, 2014
The PXG4 is still on its trip from France to Amsterdam but that's fine as we can practice the set up in theory.
Below is a diagram of the front panel. The main attractions are the two four-digit displays which will mostly show the two most interesting temperature values:
PV (Process Value) being the measured temperature in the beans as a result of the manipulations of the PID, and
SV (Set Value), the temperature level that's the current target for the PID to approach.
The tiny light of C1 indicates if the heater is on or off and when it's 50% on, the light quickly flickers on and off, showing a half-dimmed light intensity.
The SV light blinks when the heater is adding energy to raise the temperature or to keep it at the current level.
The
A/M User key
on the bottom left is used to flip through the different channels/pages of all the possible modes and settings and the
SEL
key is used to select any one of the options that can be browsed in any given mode/menu using the up/down arrow keys.
For instance, when you're in the normal operation mode and you press and hold A/M, the SV display changes to display the output value that drives the SSR and thus the heating element, between -3% and 103%.
Below is the basic map of all menus. Don't let it intimidate you too much. All details of it are explained briefly but sufficiently in the 156 pages of the manual. At first sight it may look way too complicated but as you read on and familiarize yourself with the device a little more, the map serves like the clear and simplified subway map of a big city.
It basically tells you that you dig into lower levels of the menu by holding the SEL key, on the given level you browse the options using the arrow keys, press SEL to select one and then return to the home menu by pressing A/M.
I will show the things we need to set to get going (thanks Wa'il for pointing these out).
Other settings, like a 'mask' to prevent visitors from accidentally changing any parameters in deep hidden layers of the menu structure or a password protecting these critical settings can be figured out leasurely at a later moment.
Luckily, some values and settings regarding the control of a motorized valve can be ignored on this setup. This makes the puzzle easier to solve.
The PID needs to know what's the effect of its manipulation of the heater and there are many ways to inform the PID about the temperature in the bean mass. I use a K-type thermocouple probe which happens to be the default setting, so I won't need to change it. For those who want to use a different device to communicate the resulting bean temperature, here's a list of options:
The PID switches the heater on and off to get (and keep) the beans at the desired temperature. If you use a relay switch that actually moves click-click from ON to OFF, you may want to prevent the PID switching it on and off very rapidly. You get a very precise result but also you wear out the mechanism very fast and you will be replacing the switch frequently.
Luckily, I have an SSR, a Solid State Relay that switches on and off without a physical moving part so I can afford to have it click on/off every one or two seconds.
The PID needs to know how to respond if the beans get too cool. Hit the gas or hit the brakes? For a human this is intuitive but it needs to know. We keep it on "rv--" meaning "when tamp falls, raise heat." We have no extra device to cool instead of heat and just "doing nothing" has a cooling effect.
Are we heating a kiln with pottery for many hours or beans for about ten minutes? The entire procedure of raising bean temperature, keeping it at a certain level, then raising it further and holding it there before raising more, possibly to a spike before ending the roast in a cooling session will be measured in minutes and seconds so we need to make sure the PID thinks in these time units.
The internal magic of controlling the variables of bean temperature over time, with beans decreasing in weight, bouncing around in the roasting chamber, absorbing heat one moment and radiating their own internal heat another moment, can be done by the PID controls alone which are complicated enough as they are, but one can also add the undisclosed "fuzzy logic" of the device. This will help to prevent an overshoot of a newly set SV target. If the target temperature is much higher, and the PID switches on full blast heater capacity to get there, fuzzy logic will remind it to lower the heater power in time, or else any remaining heat off the glowing red heater will make the beans hotter than one had intended.
Tip from Wa'il: It's best to first do an auto-tune (see below) without beans, then change PID control to Fuzzy and then do an auto-tune again with beans as described below.
All basics are set up now (except communication with the USB - Computer - Artisan).
We take 230g of beans to sacrifice, load the roaster, set SV to the temperature of first crack, for instance 204ºC, and when it reaches that temperature we switch on
Auto-tune
where the PID will figure out its own optimal values for P, I and D.
This Auto-tuning will take about two minutes, Wa'il told me.
After Auto-tune has succeeded, some values of the findings for P, I and D may be altered as shown below but it's probably best to let tem be for a while and get well informed before tweaking these values. For instance, if the value for P is too small, the system may become unstable and if it's too big, the response may be sluggish.
This is how I expect to wire the PID:
The
toggle switch
must be set up to be able to start the entire roasting sequence with flipping that switch.
This "digital in 1" switch can be assigned the job this way:
Before starting any operation, the PID needs to be on for 30 minutes or else it might be confused about the exact temperatures:
A to-do list suggested by Fuji, with the subjects mostly covered in these blogs:
For communications to the computer, I ordered the
PXG/PXH Serial Cable TK4H4563-E
from Fuji. It looks like this in the manual:
To provide RS232-to-USB connectivity, I ordered these from CONRAD (sorry no currently active links at their updated website):
That's it for now! It seems I'm ready for the Fuji PGX4 to arrive.
PS 13 sept 2020 some screen snapshots of my current Artisan setup pages:
Link ophalen
Facebook
X
Pinterest
E-mail
Andere apps
Reacties
Darren Addy
zei…
I realize that this is an old post, but I'm hoping that someone sees this comment. Have you ever written a post detailing how to use Artisan to no only RECORD a profile, but to DRIVE a roast (via the Fuji) using a known profile?
3 januari 2019 om 11:37
Frans
zei…
Hi Darren, yes, sure, on the fluid bed roasters where small changes in heat element power / airflow can have a fairly prompt effect, the Fuji has executed a pre-planned profile. This has been described in blog entries about the modifications on my Fracino Roastilino.
4 januari 2019 om 15:32
David
zei…
Deze reactie is verwijderd door een blogbeheerder.
4 juni 2019 om 04:08
Frans
zei…
Images work here. The links at the CONRAD webshop were indeed outdated so I deleted those. Thanks!
4 juni 2019 om 04:15
slotkavic
zei…
Hi Frans, many thanks for all your documentation. Very helpful and interesting! Could you tell me if Artisan can indeed control the PGX4 via a ‘pc loader’ cable on the underside of the PID or does it need to be via the RS-485 Modbus on the PGX4 terminal? Thank you!
2 september 2020 om 20:40
Frans
zei…
Hi Slotkavic, yes in my setup I used the 'pc loader' cable -- if I would do it again, I would probably make sure to order the type that has Modbus connectors, just to be sure.
3 september 2020 om 00:43
slotkavic
zei…
Thank you Frans. Ive been trying to get my MacBook Pro (Sierra/Artisan v 1.2) to talk nicely to my PXG4 via a Dtech RS485 / usb2 convertor but for some reason it does not want to. It seems as though I can send data from the computer to the Fuji but when I try to receive data it causes Artisan to crash.
I believe i have the correct settings (parity, baud rate etc) on the Fuji and in Artisan but when I hit the ON button I receive a Modbus error 31726 and the readings display -1. I cant for the life of me figure it out. I wonder does any of it sound familiar to you?
The Apple FTDI drivers are already installed, Artisan sees the Comm port as the USB adapter and the thermocouple reads correctly on the Fuji. Im using a twisted pair cat5e cable.
Many thanks! Mike
10 september 2020 om 23:59
Frans
zei…
Hi Mike,
Have you also tried posting on the Artisan mailing list? There's a bunch of expert users there.
I am on Artisan 2.4 here. Can you update your Artisan? It's easier to get support for the new versions -- the updates were developed for a reason ;-)
On a current Macbook Pro you would not need the special FTDI drivers as te Mac already understands the device, so in that case the drivers are maybe in the way actually. I have a 2017 Macbook Pro with MacOS catalina 10.15.6
Very early on when I was trying to get the laptop to communicate with Modbus I installed several drivers and Marko Luther of Artisan had to point out to me how to de-install those from the command line because it was a spaghetti of drivers all trying to do the same one thing.
Have you documented / illustrated your exact setup somewhere online? If so, this would probably make it easier for an expert to browse your info ans point out what to do.
Best regards,
Frans
11 september 2020 om 00:30
slotkavic
zei…
Thank you, Frans for your time! I appreciate it much :)
I have since updated to 2.4 and am still encountering modbus errors so yes, I will post / document my scenario to the mailing list today.
Many thanks again!
Mike
13 september 2020 om 10:57
Frans
zei…
Hi Mike,
Okay! I'm confident it'll get sorted then.
See you on the mailing list!
Frans
13 september 2020 om 11:14
Een reactie posten
Populaire posts van deze blog
Lose Weight, Gain Volume: About Coffee Bean Density in Artisan
-
december 21, 2014
Roasting coffee beans, you want to be as consistent as you can, replicating a successful roast while collecting enough data (besides what you see, feel, smell and taste from the coffee) to get an idea what you may be doing wrong if the results are not so good all of a sudden.   The Artisan software  for coffee roasters has a feature to help you keep track of volume and density of your beans. Density is a word for the weight of a certain volume of beans and it can be measured in grams per liter.   Your green beans are obviously more dense than the roasted beans: roasted beans have grown a lot in size and they have lost weight (moisture) in the process.    In his new book “ The Coffee Roaster’s Companion ”, the famous Scott Rao  explains these things:    “Ideally, water should account for 10.5%-11.5% of green-coffee weight.” (p.3)  “Coffee loses 12-24% of its weight during roasting, depending on initial moisture content, roast degree and inner-bean development during roasting. T...
Meer lezen
Tiny Cheap Fluid Bed Roaster by Tije and Jan
-
augustus 09, 2016
(also see Daily Coffee News feature )  Tije designed and made the following structure for a tiny and cheap fluid bed roaster, to which Jan van der Weel added the Arduino parts, electronics and programming:    Sketch by Tije de Jong          Jan sourced a very cheap blower (€ 11) to start with, Tije developed and constructed the mechanics, Jan built together and programmed the TC4 / SSR electronics.      On his blog, Jan will specify exactly how the TC4 part is combined and programmed and I will copy these details into this blog entry, just as Jan will use this video in his blog.     We did a few test roasts to make sure it works at all and it does. Towards the end, the first roast tended to get a flat BT line and airflow was slightly decreased. 200g seems max load of green beans. Second roast a little more power was given to the heater. Next we will try the Background Roast driven by the PID software of Artisan.   A week later, with updated software that works better to change the...
Meer lezen
The Four Daltons
-
juni 14, 2017
COMPAK models R120, E8, E6 and E5 lined up next to LONDINIUM L-R   First impression, notes after a visit from Roemer Overdiep:    Roemer came over to taste espressos from all 4 grinders. We made sure to every time have 18g in the 18g VST basket, using the distribution tool, getting about 30g of espresso in about 30s. R120 was best, E8 ‘redspeed’ almost as good, the E6 and E5 were somewhat similar in that the espresso was excellent but in comparison with E8 / R120 it has more ‘sharpness’ — the R120/E8 were softer, more subtle. If someone has excellent beans, an excellent espresso can be prepared with the E5 and only if one also has the bigger E8 nearby would one notice there might be something extra in buying the bigger grinder. Difference between E5 and E6 seems minimal.   These tests were done with a first roast of Kenya beans. We poured the beans from the hopper of one grinder to the other while testing and gradually the hippers got emptier.   Data about these 4 different sizes gri...
Meer lezen
Profiel bezoeken
Archiveren
februari
1
oktober
1
februari
2
augustus
3
juni
1
mei
1
april
1
maart
1
februari
5
december
3
november
8
oktober
2
september
2
augustus
5
juli
5
juni
7
mei
5
maart
2
februari
1
januari
7
december
1
november
2
oktober
1
september
2
augustus
3
juli
7
mei
2
april
14
maart
4
februari
8
januari
11
december
8
november
4
oktober
1
september
2
augustus
2
juli
3
mei
2
april
8
maart
7
februari
1
januari
4
december
1
november
2
september
4
augustus
3
juli
2
juni
6
april
2
maart
4
februari
7
januari
1
december
2
november
1
oktober
5
september
4
augustus
3
juli
1
juni
5
mei
2
april
8
maart
7
februari
13
januari
9
december
8
november
6
oktober
2
september
6
augustus
4
juli
7
juni
7
mei
4
april
5
maart
8
februari
5
januari
9
december
6
november
5
oktober
5
september
4
augustus
9
juli
3
juni
10
mei
9
april
3
maart
7
februari
7
januari
14
december
9
november
5
oktober
15
september
5
augustus
15
juli
8
juni
6
mei
5
april
4
maart
6
februari
6
januari
9
december
6
november
8
oktober
1
september
6
augustus
3
juli
7
juni
7
mei
7
april
7
maart
7
februari
8
januari
14
december
8
november
16
oktober
8
september
6
augustus
11
juli
13
juni
7
mei
12
april
3
maart
9
februari
21
januari
16
december
8
november
7
oktober
11
september
3
augustus
1
juli
3
juni
2
mei
2
april
3
maart
4
februari
3
januari
3
juni
1
mei
17
april
2
januari
2
december
2
november
1
oktober
3
augustus
4
juni
4
mei
3
april
3
maart
1
februari
1
januari
2
november
1
september
1
augustus
7
juli
2
juni
1
maart
1
februari
4
januari
2
december
1
november
4
oktober
4
september
4
augustus
4
juli
11
juni
9
mei
1
Meer tonen
Minder tonen
Misbruik rapporteren
