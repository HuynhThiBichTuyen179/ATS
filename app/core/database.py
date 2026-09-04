import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


def _build_mysql_url() -> str:
    # quote_plus xu ly mat khau chua ky tu dac biet (vd "@") de khong pha vo
    # cu phap connection string.
    password = urllib.parse.quote_plus(settings.mysql_password)
    return (
        f"mysql+pymysql://{settings.mysql_user}:{password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db}?charset=utf8mb4"
    )


def _create_engine():
    # He thong CHI dung MySQL cho moi truong dev/production that - khong con
    # co che tu dong fallback ve SQLite khi ket noi that bai (truoc day co,
    # da bo theo yeu cau nghiep vu: fallback am tham de gay nham lan ve viec
    # ung dung dang thuc su ket noi toi dau). Neu MySQL khong ket noi duoc,
    # ung dung se bao loi ro rang va dung lai ngay luc khoi dong thay vi tiep
    # tuc chay tren mot CSDL khac voi cau hinh da khai bao.
    #
    # `settings.database_url` (mac dinh SQLite) CHI con duoc dung boi
    # `tests/conftest.py` - bo test tu dong ep bien moi truong USE_MYSQL=false
    # + DATABASE_URL tro toi 1 file SQLite rieng, de moi lan chay pytest KHONG
    # dung cham toi MySQL dev/production that (fixture reset DB truoc moi test
    # se drop_all/create_all - neu chay nham vao MySQL that se xoa sach du lieu
    # that). Day la lua chon rieng cho ha tang kiem thu, khong phai mot che do
    # duoc ho tro cho ung dung that.
    if not settings.use_mysql:
        return create_engine(settings.database_url, connect_args={"check_same_thread": False})

    mysql_url = _build_mysql_url()
    mysql_engine = create_engine(
        mysql_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"connect_timeout": 5},
    )
    # Kiem tra ket noi that ngay luc khoi dong - neu MySQL server chua chay/sai
    # thong tin, that bai o day (dung ung dung ngay) thay vi that bai ro rai
    # luc request dau tien cua nguoi dung.
    with mysql_engine.connect():
        pass
    print(f"[DATABASE] Ket noi MySQL thanh cong ({settings.mysql_host}:{settings.mysql_port}/{settings.mysql_db})")
    return mysql_engine


engine = _create_engine()

# Dialect thuc te cua engine da khoi tao (khong tinh lai tu settings o noi
# khac) - id_generator.py can biet DUNG trang thai runtime: SQLite khong ho
# tro "SELECT ... FOR UPDATE" khoa hang nhu MySQL, nen khi chay tren SQLite
# (chi xay ra trong bo test, xem ghi chu o _create_engine) can them lop bao
# ve bang threading.Lock de tranh sinh trung Business ID khi nhieu test song
# song truy cap id_sequences.
is_sqlite = engine.dialect.name == "sqlite"

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
