# Bobiler Monte Yedekleyici

Amme hizmeti adına yazılmış basit bir bobiler.örg scrape edici ve medya indirici.

Yazar başına çalışır. Sevdiğiniz monteleri yedekleyebilirsiniz.

## Çalıştırma

```bash
# Önce bi virtualenv kuralım etrafı kirletmeyelim
virtualenv -p python3 env
source env/bin/activate


# Fazla bişi kullanmıyoruz. 
# requests ile url indirmece
# bs4 ile de html parsing
pip3 install -r requests bs4

# Asıl olay
python3 monte_cek.py --monteci=educatedear
```

Ornek kullanim:

![](img/educatedear.png)


Şu da benim ana sayfa olan montelem:

![](img/monte1.jpg)

Bonus

![](img/monte2.jpg)

![](img/monte3.jpg)

Yazan ve oynayan: https://twitter.com/hakanu_

