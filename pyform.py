from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import sqlite3

def recordEntry(name,corpID,BU,entry,time):
    conn = sqlite3.Connection('FaceBase.db')
    query = "INSERT INTO Employee (Name,CorpId,BU,Entry,Time)\n VALUES('%s','%s','%s','%s','%s')"%(name,corpID,BU,entry,time)
    rows = conn.execute(query)
    conn.commit()
    conn.close()

def removeEntry(corpID):
    conn = sqlite3.Connection('FaceBase.db')
    query = "INSERT INTO Employee (Name,CorpId,BU,Entry,Time)\n VALUES('%s','%s','%s','%s','%s')"%(name,corpID,BU,entry,time)
    rows = conn.execute(query)
    conn.commit()
    conn.close()
