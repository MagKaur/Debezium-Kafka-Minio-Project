from __future__ import annotations
from pathlib import Path
import os
from dataclasses import dataclass

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    BigInteger,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class CsvSpec:
    path: str
    table_name: str


def sqlalchemy_type_for_series(s: pd.Series):
    """
       Mapuje typ pandas (dtype) na typ SQLAlchemy (czyli typ w Postgresie).
       Funkcja dostaje jedną kolumnę DataFrame (Series).
    """
    dtype = s.dtype # odczyt typu danych tej kolumny w pandas

    # Jeśli pandas rozpoznaje to jako datę/czas -> w bazie użyj DateTime
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return DateTime

    # Jeśli bool -> Boolean
    if pd.api.types.is_bool_dtype(dtype):
        return Boolean

    # Jeśli int -> Integer albo BigInteger (zależnie od wartości)
    if pd.api.types.is_integer_dtype(dtype):
        try:
            # max wartości w kolumnie (skipna=True ignoruje braki)
            mx = s.max(skipna=True)

            # jeśli max > 2_147_483_647 (limit 32-bit int) -> BigInteger
            # inaczej zwykły Integer
            return BigInteger if pd.notna(mx) and mx > 2_147_483_647 else Integer
        except Exception:
            # jeśli max() się wywali (np. kolumna dziwna) -> bezpiecznie BigInteger
            return BigInteger

    # float -> Float
    if pd.api.types.is_float_dtype(dtype):
        return Float
    # fallback: jeśli nie rozpoznane -> traktuj jako tekst
    return Text


def build_table_from_dataframe(
    metadata: MetaData, # wspólny "katalog" definicji tabel
    table_name: str,    # nazwa tabeli do utworzenia
    df: pd.DataFrame,    # dane w pandas
    primary_keys: set[str] | None = None, # które kolumny są PK
    foreign_keys: dict[str, str] | None = None, # mapowanie kolumna -> "table.col"
) -> Table:
    """
    Buduje definicję tabeli SQLAlchemy dynamicznie na podstawie df.columns.

    primary_keys: zbiór nazw kolumn, które mają być PRIMARY KEY
    foreign_keys: słownik {kolumna: "ref_table.ref_column"}
    """
    # Jeśli nic nie podano, ustaw puste struktury (żeby kod dalej działał)
    primary_keys = primary_keys or set()
    foreign_keys = foreign_keys or {}

    cols = [] # tu zbieram definicje kolumn SQLAlchemy
    # Przechodzę po wszystkich kolumnach CSV (to jest "dynamiczność")
    for col_name in df.columns:
        # Zgaduję typ w bazie na podstawie danych w pandas
        col_type = sqlalchemy_type_for_series(df[col_name])

        # Sprawdzam, czy ta kolumna jest w zbiorze PK
        is_pk = col_name in primary_keys
        # Sprawdzam, czy ta kolumna ma zdefiniowany FK (jeśli nie, będzie None)
        fk_target = foreign_keys.get(col_name)

        # Jeśli kolumna ma FK, to tworzę Column z ForeignKey(...)
        if fk_target:
            col = Column(
                col_name,  # nazwa kolumny w tabeli
                col_type,  # typ SQL
                ForeignKey(fk_target), # np. "customers.customer_id"
                primary_key=is_pk,  # czy to PK
                nullable=not is_pk, # PK nie może być NULL; reszta może
            )
        else:
            # Jeśli brak FK, tworzę zwykłą Column
            col = Column(
                col_name,
                col_type,
                primary_key=is_pk,
                nullable=not is_pk,
            )

        cols.append(col) # dodaję kolumnę do listy
    # Tworzymy obiekt Table i rejestrujemy go w metadata
    return Table(table_name, metadata, *cols)


def make_engine_from_env() -> Engine:
    """
        Tworzy SQLAlchemy Engine (połączenie do Postgres) na podstawie config/.env.
        """
    # Ładuję zmienne do środowiska
    load_dotenv("config/.env")

    # Odczyt z env (z wartościami domyślnymi jeśli czegoś brakuje)
    db = os.getenv("POSTGRES_DB", "olist")
    user = os.getenv("POSTGRES_USER", "olist")
    password = os.getenv("POSTGRES_PASSWORD", "olist")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    # Składam connection string dla SQLAlchemy (postgres + sterownik psycopg2)
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    # Tworzę engine
    return create_engine(url, future=True)


def read_csv_safely(path: str) -> pd.DataFrame:
    """
       Czyta CSV do DataFrame i próbuje poprawić typy:
       - kolumny z timestamp/date -> datetime
       - kolumny "liczbowe" zapisane jako string -> numeric (ale nie *_id)
    """
    df = pd.read_csv(path) # wczytanie CSV

    # Konwersja kolumn datowych po nazwie (timestamp/date/datetime)
    for c in df.columns:
        if "timestamp" in c or c.endswith("_date") or c.endswith("_datetime"):
            # errors="coerce" -> nieparsowalne wartości zamienia na NaT zamiast error
            df[c] = pd.to_datetime(df[c], errors="coerce")
    # Próba konwersji wartości liczbowych zapisanych jako tekst
    for c in df.columns:
        # Nie dotykam *_id, bo w Olist to są identyfikatory stringowe
        if c.endswith("_id"):
            continue
        # Jeśli kolumna jest "object" (często string), spróbuje zrobić z niej liczbę
        if df[c].dtype == "object":
            # errors="ignore": jeśli nie da się przekonwertować, zostawi jak było
            df[c] = pd.to_numeric(df[c], errors="ignore")

    return df # zwracam przygotowany DataFrame


def main():
    BASEDIR = Path(__file__).resolve().parents[1]
    # Tworzy połączenie do bazy
    engine = make_engine_from_env()

    # wczytuje dane do pamięci
    customers_df = read_csv_safely(BASEDIR/"data"/"olist_customers_dataset.csv")
    products_df = read_csv_safely(BASEDIR/"data"/"olist_products_dataset.csv")
    orders_df = read_csv_safely(BASEDIR/"data"/"olist_orders_dataset.csv")

    # Definiuje tabele z PK + FK w JEDNYM metadata
    # To ważne, bo FK działają "ładnie", gdy tabele są w tym samym metadata.
    metadata = MetaData()

    # Definicja tabeli customers + ustawienie PK na customer_id
    customers_table = build_table_from_dataframe(
        metadata,
        "customers",
        customers_df,
        primary_keys={"customer_id"},
    )
    # Definicja tabeli products + ustawienie PK na product_id
    products_table = build_table_from_dataframe(
        metadata,
        "products",
        products_df,
        primary_keys={"product_id"},
    )
    # Definicja tabeli orders + PK na order_id + FK orders.customer_id -> customers.customer_id
    orders_table = build_table_from_dataframe(
        metadata,
        "orders",
        orders_df,
        primary_keys={"order_id"},
        foreign_keys={
            "customer_id": "customers.customer_id",
        },
    )

    # Tworzę schemat w bazie (drop + create)
    # engine.begin() otwiera transakcję - bezpieczniej
    with engine.begin() as conn:
        # Drop tabeli w kolejności "dziecko -> rodzic",
        # bo orders ma FK do customers (inaczej drop mógłby się wywalić).
        orders_table.drop(conn, checkfirst=True)
        products_table.drop(conn, checkfirst=True)
        customers_table.drop(conn, checkfirst=True)
        # Tworzymy wszystkie tabele z metadata (customers, products, orders)
        metadata.create_all(conn)

    # Wrzucam dane (najpierw tabele "rodzice", potem "dziecko")
    # if_exists="append" bo tabele już są utworzone, a my tylko wstawiamy wiersze.
    customers_df.to_sql("customers", engine, if_exists="append", index=False, method="multi", chunksize=10_000)
    print(f"✅ Loaded {len(customers_df):,} rows into customers")

    products_df.to_sql("products", engine, if_exists="append", index=False, method="multi", chunksize=10_000)
    print(f"✅ Loaded {len(products_df):,} rows into products")

    orders_df.to_sql("orders", engine, if_exists="append", index=False, method="multi", chunksize=10_000)
    print(f"✅ Loaded {len(orders_df):,} rows into orders")
    # Informacja końcowa
    print("🎉 Task 1 done: tables created dynamically + PK/FK constraints added + data loaded.")


if __name__ == "__main__":
    main()
