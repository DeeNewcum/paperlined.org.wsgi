This is a [WSGI server](https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface) that sits in front of all of my website's static content. It does a few duties, such as adding a standard header and converting markdown files to HTML.

[Here's the manual](https://python-markdown.github.io/#differences) for this particular Markdown renderer. Also note that there are extensions available, both [officially-sanctioned extensions](https://python-markdown.github.io/extensions/#officially-supported-extensions) as well as [third-party extensions](https://github.com/Python-Markdown/markdown/wiki/Third-Party-Extensions).

## Notes to self

* I have configured Markdown to use [mdx_linkify](https://github.com/daGrevis/mdx_linkify), which auto-links bare URLs. Mdx_linkify depends on [Mozilla Bleach](https://bleach.readthedocs.io/en/latest/), which is [deprecated](https://github.com/mozilla/bleach/issues/698) including security issues.
    * Other project's searches for a replacement for Bleach: [[1]](https://github.com/netbox-community/netbox/issues/12851) [[2]](https://github.com/django-wiki/django-wiki/discussions/1259) [[3]](https://github.com/barseghyanartur/django-fobi/issues/323) [[4]](https://github.com/MuckRock/muckrock/issues/2167) [[5]](https://github.com/philgyford/django-hines/issues/626)  
    * Possible options: [NH3](https://github.com/messense/nh3), [JustHTML](https://emilstenstrom.github.io/justhtml/bleach-migration.html)
