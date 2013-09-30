salmon-unofficial ![Salmon](https://raw.github.com/snarfed/salmon-unofficial/master/static/salmon.png)
===

  * [About](#about)
  * [Using](#using)
  * [Future work](#future-work)
  * [Development](#development)


About
---
This is a web service that implements the [Salmon](http://salmon-protocol.org/)
distributed comment protocol for Facebook, Twitter, and Google+. It's deployed
at https://salmon-unofficial.appspot.com/ .

It's part of a suite of projects that implement the [OStatus](http://ostatus.org/) federation protocols for the major social networks. The other projects include [portablecontacts-](https://github.com/snarfed/portablecontacts-unofficial), [activitystreams-](https://github.com/snarfed/activitystreams-unofficial), [webfinger-](https://github.com/snarfed/webfinger-unofficial), and [ostatus-unofficial](https://github.com/snarfed/ostatus-unofficial).

There are many related projects. [sockethub](https://github.com/sockethub/sockethub) is a similar "polyglot" approach, but more focused on writing than reading. [IndieWeb Comments](http://indiewebcamp.com/comment) are a bottom-up, decentralized approach where each user posts their comments to their own site first.

License: This project is placed in the public domain.


Using
---

Just head over to https://salmon-unofficial.appspot.com/ and connect your Facebook, Twitter, or Google+ account!


Future work
---

We're not at all confident in the interoperability and robustness. We've only done a very limited amount of testing. We should test against more Salmon-capable endpoints and fix the bugs we find.

We should probably also separate the Salmon conversion logic out of this so it can be used as a library as well as a service.

  * Allow passing OAuth tokens as keyword args.
  * Expose the initial OAuth permission flow. The hard work is already done, we just need to let users trigger it programmatically.
  * ...

We'd also love to add more sites! Off the top of my head, [YouTube](http://youtu.be/), [Tumblr](http://tumblr.com/), [WordPress.com](http://wordpress.com/), [Sina Weibo](http://en.wikipedia.org/wiki/Sina_Weibo), [Qzone](http://en.wikipedia.org/wiki/Qzone), and [RenRen](http://en.wikipedia.org/wiki/Renren) would be good candidates. If you're looking to get started, implementing a new site is a good place to start. It's pretty self contained and the existing sites are good examples to follow, but it's a decent amount of work, so you'll be familiar with the whole project by the end.


Development
---

Pull requests are welcome! Feel free to [ping me](http://snarfed.org/about) with any questions.

Most dependencies are included as git submodules. Be sure to run `git submodule init` after cloning this repo.

You can run the unit tests with `./alltests.py`. They depend on the [App Engine SDK](https://developers.google.com/appengine/downloads) and [mox](http://code.google.com/p/pymox/), both of which you'll need to install yourself.

Deploy command:
~/google_appengine/appcfg.py --oauth2 update .
