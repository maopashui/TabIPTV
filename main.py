from fastapi import FastAPI, Depends, HTTPException, responses, Request, status, Path
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlmodel import Field, Session, SQLModel, create_engine, select

SECRET_KEY = secrets.token_urlsafe(32)  # 修改本参数只会影响token，不会影响密码
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: Optional[str] = None


class UserBase(SQLModel):
    username: str
    del_tag: Optional[int] = Field(default=0)


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    cr_time: Optional[str] = Field(default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class UserCreate(UserBase):
    hashed_password: str


class TAB_PATHBASE(SQLModel):
    iptv_path: Optional[str] = None


class TAB_PATH(TAB_PATHBASE, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class TAB_PATH_UPDATE(TAB_PATHBASE):
    iptv_path: Optional[str] = None


class TabBase(SQLModel):
    group_title: Optional[str] = Field(default="-")
    tvg_id: str
    tvg_logo: str
    tvg_name: str
    tvg_url: str
    up_time: Optional[str] = Field(default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    del_tag: Optional[int] = Field(default=0)


class Tab(TabBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cr_time: Optional[str] = Field(default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class TabCreate(TabBase):
    pass


class TabRead(TabBase):
    id: int
    cr_time: str


class TabUpdate(TabBase):
    group_title: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_logo: Optional[str] = None
    tvg_name: Optional[str] = None
    tvg_url: Optional[str] = None
    up_time: Optional[str] = None
    del_tag: Optional[int] = None


sqlite_file_name = "tabdata.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(docs_url=None, redoc_url=None)
app.mount("/statics", StaticFiles(directory="statics"), name="statics")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db['username']:
        # user_dict = db[username]
        # print(user_dict)
        return db


def authenticate_user(fake_db, username: str, password: str):
    # print(fake_db)
    user = get_user(fake_db, username)
    # print(user)
    # print(user['password'])
    # print(get_password_hash(user['password']))
    if not user:
        return False
    if not verify_password(password, user['password']):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(*, session: Session = Depends(get_session), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    users_db = session.exec(select(User).where(User.username == token_data.username and User.del_tag == "0")).one()
    fake_users_db = {"username": users_db.username, "password": users_db.hashed_password, "del_tag": users_db.del_tag}
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user['del_tag'] == "1":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.get("/{iptv_path}/{msg_type}", response_class=responses.PlainTextResponse)
async def get_iptvstr(*, session: Session = Depends(get_session), iptv_path: str = Path(...), msg_type: str):
    iptv_path1 = session.exec(select(TAB_PATH).where(TAB_PATH.iptv_path == iptv_path).limit(1)).first()
    print(iptv_path1)
    if not iptv_path1:
        raise HTTPException(status_code=404, detail="TabIPTV page not found")
    Tabs = session.exec(select(Tab)).all()
    if not Tabs:
        raise HTTPException(status_code=404, detail="TabIPTV page not found")
    if msg_type == "m3u":
        m3u_str = "#EXTM3U\n"
        for t in Tabs:
            """
            #EXTM3U
            #EXTINF:-1 group-title="央视台" tvg-id="CCTV-1" tvg-logo="https://live.fanmingming.com/tv/CCTV1.png",CCTV-1 综合
            http://39.134.24.162/dbiptv.sn.chinamobile.com/PLTV/88888890/224/3221225804/index.m3u8
            """
            # print(t.tvg_url)
            group_title = t.group_title
            tvg_id = t.tvg_id
            tvg_logo = t.tvg_logo
            tvg_name = t.tvg_name
            tvg_url = t.tvg_url
            m3u_str += f"""#EXTINF:-1 group-title="{group_title}" tvg-id="{tvg_id}" tvg-logo="{tvg_logo}",{tvg_name}\n{tvg_url}\n"""
        # print(type(m3u_str))
        return m3u_str
    else:
        """
        央视台,#genre#
        CCTV-1 综合,http://39.134.24.162/dbiptv.sn.chinamobile.com/PLTV/88888890/224/3221225804/index.m3u8
        衛視台,#genre#
        江蘇台,http://39.134.24.162/dbiptv.sn.chinamobile.com/PLTV/88888890/224/3221225804/index.m3u8
        """
        grouped_data = {}

        # 分组并拼接数据
        for t in Tabs:
            group_title = t.group_title
            tvg_name = t.tvg_name + "," + t.tvg_url

            if group_title not in grouped_data:
                grouped_data[group_title] = [tvg_name]
            else:
                grouped_data[group_title].append(tvg_name)

        # 将每个分组内的名字拼接成一个字符串
        txt_str = '\n'.join(
            [f"{group_title},#genre#\n{'+'.join(tvg_name)}" for group_title, tvg_name in grouped_data.items()])
        return txt_str


@app.post("/tabs", response_model=TabRead)
async def insert_tab(*, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user),
                     tab: TabCreate):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tab = Tab.model_validate(tab)
    session.add(tab)
    session.commit()
    session.refresh(tab)
    return tab


@app.get("/tabs", response_model=List[TabRead])
async def read_tabs(*, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user),
                    page: Optional[int] = 1, perPage: Optional[int] = 10):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not page:
        Tabs = session.exec(select(Tab).where(Tab.del_tag == "0")).all()
        return Tabs
    else:
        Tabs = session.exec(select(Tab).where(Tab.del_tag == "0").offset((page - 1) * perPage).limit(perPage)).all()
        return Tabs


@app.get("/tabs/{tab_id}", response_model=TabRead)
async def read_tab(*, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user),
                   tab_id: int):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tab = session.get(Tab, tab_id)
    if not tab:
        raise HTTPException(status_code=404, detail="Tab not found")
    return tab


@app.patch("/tabs/{tab_id}", response_model=TabRead)
async def update_tab(*, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user),
                     tab_id: int, TabU: TabUpdate):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db_Tab = session.get(Tab, tab_id)
    if not db_Tab:
        raise HTTPException(status_code=404, detail="TabIPTV id not found")
    Tab_data = TabU.model_dump(exclude_unset=True)
    db_Tab.sqlmodel_update(Tab_data)
    db_Tab.up_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session.add(db_Tab)
    session.commit()
    session.refresh(db_Tab)
    return db_Tab


@app.delete("/tabs/{tab_id}")
async def delete_tab(*, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user),
                     tab_id: int):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tab = session.get(Tab, tab_id)
    if not tab:
        raise HTTPException(status_code=404, detail="Tab not found")
    session.delete(tab)
    session.commit()
    return {"ok": True}


@app.post("/urledit")
async def update_url(*, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user),
                     url: str, id: int):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db_Tab = session.get(Tab, id)
    if not db_Tab:
        raise HTTPException(status_code=404, detail="TabIPTV url not found")
    db_Tab.tvg_url = url


@app.get("/index", response_class=HTMLResponse)
async def tab_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/login", response_class=HTMLResponse)
async def tab_login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

@app.get("/register", response_class=HTMLResponse)
async def tab_register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )

@app.post("/token")
async def login_for_access_token(*, session: Session = Depends(get_session),
                                 form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    users_db = session.exec(select(User).where(User.username == form_data.username and User.del_tag == "0")).one()
    # print(form_data.username)
    # print(fake_users_db)
    fake_users_db = {"username": users_db.username, "password": users_db.hashed_password}
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/users", response_model=UserBase)
async def insert_user(*, session: Session = Depends(get_session), user: UserCreate):
    user_num = session.exec(select(User)).all()
    if len(user_num) > 0:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = User.model_validate(user)
    new_user.hashed_password = get_password_hash(user.hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@app.get("/tab_path", response_model=List[TAB_PATHBASE])
async def get_tab_path(*, session: Session = Depends(get_session),
                       current_user: User = Depends(get_current_active_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session.exec(select(TAB_PATH)).all()


@app.post("/tab_path", response_model=TAB_PATHBASE)
async def insert_tab_path(*, session: Session = Depends(get_session), tab_path: TAB_PATHBASE,
                          current_user: User = Depends(get_current_active_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tab_path = TAB_PATH.model_validate(tab_path)
    session.add(tab_path)
    session.commit()
    session.refresh(tab_path)
    return tab_path


@app.patch("/tab_path/{id}", response_model=TAB_PATHBASE)
async def update_tab_path(*, session: Session = Depends(get_session), tab_path_u: TAB_PATH_UPDATE, id: int,
                          current_user: User = Depends(get_current_active_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tab_path_old = session.get(TAB_PATH, id)
    if not tab_path_old:
        raise HTTPException(status_code=404, detail="TabIPTV path not found")
    tab_path = tab_path_u.model_dump(exclude_unset=True)
    tab_path_old.sqlmodel_update(tab_path)
    session.add(tab_path_old)
    session.commit()
    session.refresh(tab_path_old)
    return tab_path_old


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    # print(current_user)
    return current_user
