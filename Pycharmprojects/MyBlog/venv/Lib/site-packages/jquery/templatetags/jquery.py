# -*- coding: utf-8 -*-

from appconf import AppConf
from django import template
from django.conf import settings
from django.template.base import TextNode

from .. import jq_version


register		 = template.Library()


class _AppConf(AppConf):
	VERSION				 = jq_version
	CDN					 = False
	DEFAULT_CDN			 = 'http://code.jquery.com/jquery-%(version)s.min.js'

	STATIC_JS			 = '%(static_url)sjquery/jquery-%(version)s.min.js'

	SCRIPT_TAG			 = '<script type="text/javascript" src="%(url)s"></script>'

	class Meta:
		prefix			 = "JQUERY"  # appconf cannot determine the prefix here!



@register.tag
def jquery_js(parser, token):
	bits	 = tuple(token.split_contents()) + (None, None)
	version	 = bits[1] or settings.JQUERY_VERSION
	cdn		 = settings.JQUERY_CDN
	if cdn:
		if cdn is True:
			cdn = settings.JQUERY_DEFAULT_CDN
		url	 = cdn % {'version': version}
	else:
		url	 = settings.JQUERY_STATIC_JS % {
			'static_url': settings.STATIC_URL, 'version': version}

	res	 = settings.JQUERY_SCRIPT_TAG % {'url': url}
	return TextNode(res)

