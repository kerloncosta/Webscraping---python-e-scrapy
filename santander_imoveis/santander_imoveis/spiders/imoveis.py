import scrapy
import re
import time
import json
from scrapy.http import Request
from random import choice
from geopy.geocoders import Nominatim

# !!! Instruções para Configuração do projeto !!!
# Antes de rodar o programa, execute o seguinte comando no terminal para instalar todas as dependências necessárias:
# pip install -r requirements.txt


class MovelSpider(scrapy.Spider):
    name = "imovel"
    start_urls = [
        "https://www.santanderimoveis.com.br/venda/imovel/casa-a-venda-na-rua-lamartine-babo-paulinia-sp-codigo-6663-santander-imoveis/",
    ]

    # Método para iniciar as requisições, utilizando diferentes user agents para evitar bloqueios
    def start_requests(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.3 Safari/602.3.12',
        ]
        for url in self.start_urls:
            yield Request(url, headers={'User-Agent': choice(user_agents)})

    def parse(self, response):

        for imoveis in response.css('body'):

            # ---------------------------- # ---------------------------- #
            # Extração de dados da página que não precisam ser manipulados

            title = imoveis.css('section.main-top h1::text').get()

            auctioneer = imoveis.css(
                'section.main-atendimento div strong::text').get()

            description = imoveis.css('section.main-info li::text').get()

            registry = imoveis.css(
                'section.main-info p:nth-of-type(2) strong::text').get()

            registration = imoveis.css(
                'section.main-info p strong::text').get()

            source_id = imoveis.css('span.badge::text').get()
            source_id = source_id[6:14]

            # ---------------------------- # ---------------------------- #
            # Extração e formatação do valor de avaliação e do valor do imóvel

            evaluation = re.findall(
                r'\d+', imoveis.css('div.values-line-values div:nth-of-type(2) strong::text').get())
            evaluation = ''.join(evaluation)

            value = re.findall(
                r'\d+', imoveis.css('div.values-line-values div strong::text').get())
            value = ''.join(value)

            # ---------------------------- # ---------------------------- #
            # Verificação se o imóvel está ocupado

            is_vacant_text = imoveis.css(
                'section.main-top div strong::text').get()
            is_vacant = False if 'ocupado' in is_vacant_text.lower() else True

            # ---------------------------- # ---------------------------- #
            # Extração e formatação da data

            date = response.css('p::text').re_first(
                r'\d{2}/\d{2}/\d{4} - \d{2}:\d{2}')
            if date:
                date = re.sub(
                    r'(\d{2})/(\d{2})/(\d{4}) - (\d{2}):(\d{2})', r'\3-\2-\1T\4:\5:00', date)

            # ---------------------------- # ---------------------------- #
            # Extração da URL do anunciante

            target_url = imoveis.css(
                'section.main-atendimento div a::attr(href)').get()

            auctioneer_url = re.match(r'https?://[^/]+', target_url).group(0)

            # ---------------------------- # ---------------------------- #
            # Extração do tipo de imóvel

            property_type = imoveis.css('section.main-top h1::text').get()
            property_type = re.match(r'[^\s]+', property_type).group(0)

            # ---------------------------- # ---------------------------- #
            # Extração e formatação da área do imóvel

            area = imoveis.css(
                'section.main-info p:nth-of-type(4) strong::text').get()

            land_area = area[0:3]
            total_area = area[22:25]

            # ---------------------------- # ---------------------------- #
            # Extração da URL da imagem do imóvel a partir do script JSON-LD

            script_tag = response.css(
                'script[type="application/ld+json"]::text').get()

            data = json.loads(script_tag)

            image_url = None
            for item in data['@graph']:
                if item['@type'] == 'ImageObject':
                    image_url = item['url']

            # ---------------------------- # ---------------------------- #
            # Extração e formatação do endereço do imóvel

            place_property = imoveis.css('section.main-top p::text').get()

            address = place_property[0:23]
            neighborhood = place_property[106:116]
            city = place_property[118:126]
            state = place_property[129:131]
            zip_code = place_property[138:146]

            # Função para obter as coordenadas do imóvel usando geopy
            def get_lat_long(full_address):
                geolocator = Nominatim(user_agent="Aplication_property")
                location = geolocator.geocode(full_address)
                if location:
                    return location.latitude, location.longitude
                else:
                    return None, None

            full_address = f"{address}, 
            {neighborhood}, {city}, {state}, Brazil"
            latitude, longitude = get_lat_long(full_address)
            time.sleep(1)

            # ---------------------------- # ---------------------------- #
            # Retorno dos dados extraídos e formatados

            yield {
                'title': title,
                'evaluation': evaluation,
                'value': value,
                'date': date,
                'property_type': property_type,
                'rooms': 0,
                'parking_spots': 0,
                'private_area': 0,
                'land_area': land_area,
                'total_area': total_area,
                'auctioneer': auctioneer,
                'auctioneer_url': auctioneer_url,
                'target_url': target_url,
                'is_vacant': is_vacant,
                'description': description,
                'registry': registry,
                'registration': registration,
                'image_url': image_url,
                'state': state,
                'city': city,
                'neighborhood': neighborhood,
                'address': address,
                'zip_code': zip_code,
                'latitude': latitude,
                'longitude': longitude,
                'source_id': source_id,
                'source_url': response.url,
            }
