import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta
from dateutil import parser, tz

# work on date logic - timeframe

def date_parser(date):
 if date == date:
  return parser.parse(date)

def gantt(df, start_date, end_date, priorities, integrations):
 df = df[(df['date_created'] >= start_date) & (df['date_created'] <= end_date)]
 df = df[df['priority_num'].isin(priorities) & df['integrations'].isin(integrations)]
 df = df[df['open_closed'] == 'closed']

 return px.timeline(df, x_start="date_created", x_end="date_closed", y="integrations", color="priority_text",
                    width=1200, height=1200, color_discrete_sequence=px.colors.sequential.YlOrRd_r[::2],
                    category_orders={'priority_text': ["urgent", "high", "normal", "low"]})


def created_vs_closed_tickets(df, timeframe, start_date, end_date, priorities, integrations):
 time_cre = 'created_' + timeframe

 df = df[(df['date_created'] >= start_date) & (df['date_created'] <= end_date)]
 df = df[df['priority_num'].isin(priorities) & df['integrations'].isin(integrations)]

 df_cre_quarter = df[['name', time_cre]].groupby([time_cre]).count().reset_index()
 df_cre_quarter.rename(columns={time_cre: timeframe}, inplace=True)
 df_cre_quarter["status"] = "tickets opened"

 time_clo = 'closed_' + timeframe
 df_clo_quarter = df[['name', time_clo]].groupby([time_clo]).count().reset_index()
 df_clo_quarter.rename(columns={time_clo: timeframe}, inplace=True)
 df_clo_quarter["status"] = "tickets closed"

 df_creclo = df_cre_quarter.append(df_clo_quarter)

 return px.bar(df_creclo, x=timeframe, y="name",
                     color='status', barmode='group',
                     height=400)

def cycle_waiting(df, timeframe, start_date, end_date, priorities, integrations):
 df = df[(df['date_created'] >= start_date) & (df['date_created'] <= end_date)]
 df = df[df['priority_num'].isin(priorities) & df['integrations'].isin(integrations)]
 df = df[df['open_closed'] == 'closed']

 df['waiting_time'] = df['date_progress'] - df['date_created']
 df['cycle_time'] = df['date_closed'] - df['date_progress']
 df['waiting_time'] = df['waiting_time'].apply(lambda x: x.total_seconds() / 3600)
 df['cycle_time'] = df['cycle_time'].apply(lambda x: x.total_seconds() / 3600)

 time_name = 'created_' + timeframe

 df_cycle = df[[time_name, 'cycle_time']].groupby(time_name).mean().reset_index()
 df_waiting = df[[time_name, 'waiting_time']].groupby(time_name).mean().reset_index()

 df_cycle['status'] = 'cycle time'
 df_waiting['status'] = 'waiting time'

 df_cycle.rename(columns={'cycle_time': 'time'}, inplace=True)
 df_waiting.rename(columns={'waiting_time': 'time'}, inplace=True)

 return px.bar(df_cycle.append(df_waiting), x=time_name, y="time",
               color='status', barmode='stack',
               height=400)


def crit_vs_noncrit(df, timeframe, start_date, end_date, priorities, integrations):
 df = df[(df['date_created'] >= start_date) & (df['date_created'] <= end_date)]
 df = df[df['priority_num'].isin(priorities) & df['integrations'].isin(integrations)]

 time_name = 'created_' + timeframe

 df['critical'] = df['priority_num'].apply(lambda x: 1 if x < 3 else 0)
 df['non_critical'] = df['priority_num'].apply(lambda x: 1 if x > 2 else 0)

 df_crit_ratio = df.groupby(time_name).sum().reset_index()
 df_crit_ratio['critical_per'] = df_crit_ratio['critical'] / (
          df_crit_ratio['critical'] + df_crit_ratio['non_critical']) * 100
 df_crit_ratio['non_critical_per'] = df_crit_ratio['non_critical'] / (
          df_crit_ratio['critical'] + df_crit_ratio['non_critical']) * 100
 df_crit_ratio['full'] = 100

 df_uncrit_ratio = df_crit_ratio.copy()
 df_crit_ratio['crit_vs_non'] = "critical"
 df_uncrit_ratio['crit_vs_non'] = "non-critical"

 df_crit_ratio['percent'] = df_crit_ratio['critical_per']
 df_uncrit_ratio['percent'] = df_uncrit_ratio['non_critical_per']

 return px.bar(data_frame=df_crit_ratio.append(df_uncrit_ratio), x=time_name, y='percent', color="crit_vs_non",
               barmode="stack")


def avg_issues_devs(df, timeframe, start_date, end_date, priorities, integrations):
 df = df[(df['date_created'] >= start_date) & (df['date_created'] <= end_date)]
 df = df[df['priority_num'].isin(priorities) & df['integrations'].isin(integrations)]

 time_name = "created_" + timeframe

 df_closed_dev = df.groupby(time_name).agg({"name": 'count', 'assigned_dev_new': pd.Series.nunique}).reset_index()
 df_closed_dev['avg_close_dev'] = df_closed_dev['name'] / df_closed_dev['assigned_dev_new']

 return px.bar(data_frame=df_closed_dev, x=time_name, y="avg_close_dev")

def developers_ticket(df, timeframe, start_date, end_date, priorities, integrations):
 df = df[(df['date_created'] >= start_date) & (df['date_created'] <= end_date)]
 df = df[df['priority_num'].isin(priorities) & df['integrations'].isin(integrations)]

 time_name = "created_" + timeframe
 df_devs = df.groupby(['assigned_dev_new', 'created_quarter']).count().reset_index()

 return px.bar(data_frame=df_devs, x='assigned_dev_new', y='name', color='created_quarter', barmode="group")

def integrations_tickets_time(df, timeframe, start_date, end_date, priorities, integrations):
 df = df[(df['date_created'] >= start_date) & (df['date_created'] <= end_date)]
 df = df[df['priority_num'].isin(priorities) & df['integrations'].isin(integrations)]

 time_name = "created_" + timeframe
 # revisit again later
 #time_name = "created_quarter"

 df_tickets_int = df.groupby(["integrations", time_name]).count().reset_index()
 df_tickets_int[time_name] = df_tickets_int[time_name].apply(lambda x: str(x))

 return px.bar(data_frame=df_tickets_int, x='integrations', y="name",  color=time_name, barmode='group',
                    category_orders={time_name: ["1", "2", "3", "4"]}, width=1500)

def integrations_critical(df, timeframe, start_date, end_date, priorities, integrations):
 df = df[(df['date_created'] >= start_date) & (df['date_created'] <= end_date)]
 df = df[df['priority_num'].isin(priorities) & df['integrations'].isin(integrations)]

 time_name = "created_" + timeframe

 df_integrations = df.groupby(["integrations", 'priority_num']).count().reset_index().sort_values('name')
 df_sort_int = df.groupby(["integrations"]).count().reset_index().sort_values(by="name")[['integrations', 'name']]
 df_sort_int.rename(columns={'name': 'total'}, inplace=True)
 df_integrations2 = df_integrations.merge(df_sort_int, on='integrations', how='left').sort_values(
  by=['total', "priority_num"])
 # df_integrations2['priority_text'] = df_integrations2['priority_num'].apply(lambda x: prio_dict_back[x])
 # df_integrations2['priority_num'] = df_integrations2['priority_num'].apply(lambda x: str(x))

 return px.bar(data_frame=df_integrations2, x='name', y='integrations', color='priority_num', orientation='h', barmode="stack", height=1000
               #, color_discrete_sequence=px.colors.sequential.YlOrRd_r[::2]
               #, category_orders={'priority_num': ["1", "2", "3", "4"]}
               )

if __name__ == '__main__':
 st.set_page_config(layout="wide")

 df = pd.read_csv('hai_clickup_fake3.csv')
 df['date_created'] = df['date_created'].apply(lambda x: date_parser(x))
 df['date_closed'] = df['date_closed'].apply(lambda x: date_parser(x))
 df['date_progress'] = df['date_progress'].apply(lambda x: date_parser(x))
 st.dataframe(df.head())

 timeframe = st.sidebar.radio("Timeframe", ["Quarter", 'Month', 'Week']).lower()

 start_date = st.sidebar.date_input(
     "Starting from...",
  (datetime.today() - relativedelta(months=6)))
 start_date = datetime(start_date.year, start_date.month, start_date.day, tzinfo=pytz.utc)

 end_date = st.sidebar.date_input(
        "Until...",
        datetime.today())
 end_date = datetime(end_date.year, end_date.month, end_date.day, tzinfo=pytz.utc)

 priorities = st.sidebar.multiselect(
        'Priorities',
        ['Urgent', 'High', 'Normal', 'Low'], default=['Urgent', 'High', 'Normal', 'Low'])
 prio_dict = {
  "Urgent": 1,
  "High": 2,
  "Normal": 3,
  "Low": 4
 }
 prio_dict_back = {
  1: "Urgent",
  2: "High",
  3: "Normal",
  4: "Low"
 }
 priorities = [prio_dict[i] for i in priorities]

 integrations = st.sidebar.multiselect(
        'Integrations',
        ['airtable',
         'amazon advertising api',
         'amazon seller central',
         'apple search ad',
         'asana',
         'azure data storage',
         'azure sql',
         'bing ad',
         'braintree',
         'chargebee',
         'cloud storage',
         'criteo',
         'csv',
         'datos survey',
         'exchange rate api',
         'facebook ad',
         'facebook pages',
         'file cloud',
         'freshdesk',
         'freshsales',
         'google ad',
         'google analytics',
         'google bigquery',
         'google sheet',
         'hubspot',
         'instagram',
         'klaviyo',
         'lever',
         'linkedin ad',
         'mongo db',
         'mysql',
         'netsuite',
         'office 365 sharepoint',
         'outbrain',
         'paypal',
         'pinterest ad',
         'pipedrive',
         'postgres',
         'recharge',
         's3',
         'salesforce',
         'sap',
         'sftp',
         'shopify',
         'snapchat',
         'stripe',
         'taboola',
         'tiktok',
         'twitter ad',
         'typeform',
         'xero',
         'xlsx',
         'yahoo gemini',
         'zendesk',
         'mssql',
         'postgres',
         'mailchimp',
         'youtube',
         'clickup'
         # , np.nan
         ], default=['airtable',
 'amazon advertising api',
 'amazon seller central',
 'apple search ad',
 'asana',
 'azure data storage',
 'azure sql',
 'bing ad',
 'braintree',
 'chargebee',
 'cloud storage',
 'criteo',
 'csv',
 'datos survey',
 'exchange rate api',
 'facebook ad',
 'facebook pages',
 'file cloud',
 'freshdesk',
 'freshsales',
 'google ad',
 'google analytics',
 'google bigquery',
 'google sheet',
 'hubspot',
 'instagram',
 'klaviyo',
 'lever',
 'linkedin ad',
 'mongo db',
 'mysql',
 'netsuite',
 'office 365 sharepoint',
 'outbrain',
 'paypal',
 'pinterest ad',
 'pipedrive',
 'postgres',
 'recharge',
 's3',
 'salesforce',
 'sap',
 'sftp',
 'shopify',
 'snapchat',
 'stripe',
 'taboola',
 'tiktok',
 'twitter ad',
 'typeform',
 'xero',
 'xlsx',
 'yahoo gemini',
 'zendesk',
 'mssql',
 'postgres',
 'mailchimp',
 'youtube',
 'clickup'
 #, np.nan
])


 # writing in the app
 st.title('Integrations Engineering Dashboard')

 st.subheader('Gantt Chart - Tickets for each Integration')
 st.plotly_chart(gantt(df, start_date, end_date, priorities, integrations))

 st.subheader('Breakdown Tickets closed by Developers')
 st.plotly_chart(px.bar(data_frame=df.groupby(['assigned_dev_new', 'created_quarter']).count().reset_index(), x='assigned_dev_new', y='name', color='created_quarter', barmode="group"))

 st.subheader('Total Tickets per Integration segmented by Time')
 with st.expander("Open to see Integrations"):
  integrations2 = st.multiselect(
   'Integrations for this table',
   ['airtable',
    'amazon advertising api',
    'amazon seller central',
    'apple search ad',
    'asana',
    'azure data storage',
    'azure sql',
    'bing ad',
    'braintree',
    'chargebee',
    'cloud storage',
    'criteo',
    'csv',
    'datos survey',
    'exchange rate api',
    'facebook ad',
    'facebook pages',
    'file cloud',
    'freshdesk',
    'freshsales',
    'google ad',
    'google analytics',
    'google bigquery',
    'google sheet',
    'hubspot',
    'instagram',
    'klaviyo',
    'lever',
    'linkedin ad',
    'mongo db',
    'mysql',
    'netsuite',
    'office 365 sharepoint',
    'outbrain',
    'paypal',
    'pinterest ad',
    'pipedrive',
    'postgres',
    'recharge',
    's3',
    'salesforce',
    'sap',
    'sftp',
    'shopify',
    'snapchat',
    'stripe',
    'taboola',
    'tiktok',
    'twitter ad',
    'typeform',
    'xero',
    'xlsx',
    'yahoo gemini',
    'zendesk',
    'mssql',
    'postgres',
    'mailchimp',
    'youtube',
    'clickup'
    # , np.nan
    ], default=["shopify", "zendesk", "google ad"])
 st.plotly_chart(integrations_tickets_time(df, timeframe, start_date, end_date, priorities, integrations2))

 st.subheader('Total Tickets by Integration & Priority')
 st.plotly_chart(integrations_critical(df, timeframe, start_date, end_date, priorities, integrations))

 col1, col2 = st.columns(2)

 with col1:
  st.subheader('Total Tickets - create vs close')
  st.plotly_chart(created_vs_closed_tickets(df, timeframe, start_date, end_date, priorities, integrations))

  st.subheader('Tickets - Critical vs. Non-Critical')
  st.plotly_chart(crit_vs_noncrit(df, timeframe, start_date, end_date, priorities, integrations))

 with col2:
  st.subheader('Cycle & Waiting Time')
  st.plotly_chart(cycle_waiting(df, timeframe, start_date, end_date, priorities, integrations))

  st.subheader('Avg issues per Dev')
  st.plotly_chart(avg_issues_devs(df, timeframe, start_date, end_date, priorities, integrations))

