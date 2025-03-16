from dataclasses import dataclass
from typing import Optional

@dataclass
class TableHeader(object):
    name: str
    sort: Optional[int] = None

def make_table_header(header_list):
    headers = []
    for header in header_list:
        headers.append(TableHeader(header))
    return (headers)

if __name__ == "__main__":
    print (make_table_header(["test"]))