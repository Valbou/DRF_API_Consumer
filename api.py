import asyncio
import requests
from functools import partial


class Api:
    """ Base class to consume Django REST Framework APIs """
    token = ''
    url = ''
    output = 'json'
    prev = None
    next = None
    headers = {'user-agent': 'Vb API', 'content-type': 'application/json; charset=utf8'}

    def config(self, url, token='', secure=True, output='json', verbose=False):
        self.url = url
        self.secure = secure
        self.token = token
        self.output = output
        self.verbose = verbose

    async def async_req(self, funct, **kargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(funct, **kargs))

    def get_list(self, item, options=[], page=None):
        # DRF pagination management
        if page is "next" and self.next:
            url = self.next
        elif page is "prev" and self.prev:
            url = self.prev
        elif page is None:
            self.prev = None
            self.next = None
            url = self._gen_url(item, options=options)
        else:
            return False

        r = asyncio.run(self.async_req(
            funct=requests.get, 
            url=url, 
            headers=self.headers
        ))

        if r.status_code == 200:
            datas = r.json()
            self.prev = datas['previous']
            self.next = datas['next']
            return datas['results']
        else:
            self.debug(item, r)
        return False

    def get_inst(self, item, id_instance, options=[]):
        r = asyncio.run(self.async_req(
            funct=requests.get, 
            url=self._gen_url(item, id_instance=id_instance, options=options), 
            headers=self.headers)
        )
        if r.status_code == 200:
            return r.json()
        else:
            self.debug(item, r)
        return False

    def post_inst(self, item, payload={}, options=[]):
        r = asyncio.run(self.async_req(
            funct=requests.post,
            url=self._gen_url(item, options=options),
            headers=self.headers,
            json=payload,
        ))
        if r.status_code != 201:
            self.debug(item, r)
            return False
        return r.json()

    def put_inst(self, item, payload={}, options=[]):
        id_instance = payload.get('id', None)
        if id_instance:
            r = asyncio.run(self.async_req(
                funct=requests.put,
                url=self._gen_url(item, id_instance=id_instance, options=options),
                headers=self.headers,
                json=payload
            ))
            if r.status_code != 200:
                self.debug(item, r)
            return r.json()
        return False

    def patch_inst(self, item, payload={}, options=[]):
        id_instance = payload.get('id', None)
        if id_instance:
            r = asyncio.run(self.async_req(
                funct=requests.patch,
                url=self._gen_url(item, id_instance=id_instance, options=options),
                headers=self.headers,
                json=payload
            ))
            if r.status_code != 200:
                self.debug(item, r)
            return r.json()
        return False

    def delete_inst(self, item, payload={}, options=[]):
        id_instance = payload.get('id', None)
        r = asyncio.run(self.async_req(
            funct=requests.delete,
            url=self._gen_url(item, id_instance=id_instance, options=options),
            headers=self.headers,
            data=payload
        ))
        if r.status_code != 204:
            self.debug(item, r)
            return False
        return True

    def debug(self, item, r):
        complement = ''
        if self.verbose:
            complement = "\nErr {} {}\n{}\n##########\n{}\n##########".format(r.request.method, r.status_code, r.url, r.content)
        else:
            complement = " - Err {} {}".format(r.request.method, r.status_code)
        err = "API error ({}){}".format(item, complement)
        raise Exception(err)

    def __str__(self):
        return "{} {}".format(self.url, self.token)

    def _gen_url(self, item, id_instance='', options=[]):
        return '{}{}/{}/{}?token={}&format={}{}'.format(('https://' if self.secure else 'http://'), self.url, item, id_instance, self.token, self.output, self._options(options))

    def _options(self, options):
        return ("&" + "&".join(options)) if len(options) else ""

