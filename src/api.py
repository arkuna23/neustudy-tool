from dataclasses import dataclass

from aiohttp import ClientSession

from src.util import filter_fields

from .consts import *


class UnauthorizedException(Exception):
    pass


@dataclass
class TeachTerm:
    id: str
    name: str
    termStartTime: tuple[int, int, int]
    termEndTime: tuple[int, int, int]

@dataclass
class Course:
    id: str
    teacherId: str
    teacherName: str
    termId: str
    termName: str
    courseId: str
    courseName: str
    teachClassId: str
    className: str


async def get_terms(session: ClientSession) ->  list[TeachTerm]:
    response = await session.get(
        f"{URL_BASE}/teachmanager/teach-dropdown/getTeachTermDropDown"
    )
    data = await response.json()
    return [TeachTerm(**filter_fields(term, TeachTerm)) for term in data["data"]]

async def get_courses(
    session: ClientSession,
    page_no: int = 1,
    page_size: int = 10,
    term_id: str|None = None
) -> tuple[list[Course], int]:
    params: dict[str, int|str] = {
        "pageNo": page_no,
        "pageSize": page_size,
    }
    if term_id:
        params["termId"] = term_id

    response = await session.get(
        f"{URL_BASE}/teachmanager/teach-arrangement-stu/page",
        params = params
    )
    data = await response.json()
    if data['code'] == 401:
        raise UnauthorizedException()
    data = data['data']
    return [Course(**filter_fields(course, Course)) for course in data["list"]], data["total"]

async def get_all_courses(session: ClientSession) -> list[Course]:
    courses, total = await get_courses(session, 1, 100)
    for page_no in range(2, total // 100 + 2):
        courses += (await get_courses(session, page_no, 100))[0]
    return courses

async def get_sign_num(session: ClientSession, stu_id: str, teach_class_id: str) -> int:
    response = await session.get(
        f"{URL_BASE}/teachmanager/teach-course-attendance-detail/getSignNum",
        params = {
            "studentId": stu_id,
            "teachClassId": teach_class_id
        }
    )
    data = await response.json()
    if data['code'] == 401:
        raise UnauthorizedException()
    return data['data']['unSignNum']

@dataclass
class SignRecord:
    id: str|None
    attendanceId: str|None


async def get_sign_record(session: ClientSession, stu_id: str, teach_class_id: str) -> SignRecord:
    response = await session.get(
        f"{URL_BASE}/teachmanager/teach-course-attendance-detail/getSignRecord",
        params = {
            "studentId": stu_id,
            "teachClassId": teach_class_id
        }
    )
    data = await response.json()
    if data['code'] == 401:
        raise UnauthorizedException()
    return SignRecord(**filter_fields(data['data'], SignRecord))

async def sign(session: ClientSession, record: SignRecord, user_id: str):
    response = await session.put(
        f"{URL_BASE}/teachmanager/teach-course-attendance-detail/update",
        json = {
            "id": record.id,
            "attendanceId": record.attendanceId,
            "studentId": user_id,
            "signRole": 4,
            "signUserId": user_id,
            "status": 1
        }
    )
    data = await response.json()
    match data['code']:
        case 401:
            raise UnauthorizedException()
        case code if code != 0:
            raise Exception(f"Failed to sign: {data}")

async def get_unread_count(session: ClientSession) -> int:
    response = await session.get(f"{URL_BASE}/system/notify-target/get-unread-count")
    data = await response.json()
    if data['code'] == 401:
        raise UnauthorizedException()
    return data['data']
