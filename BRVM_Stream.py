import streamlit as st,pandas as pd,numpy as np,os,random as rd,datetime as dt,plotly.express as px
from streamlit.components.v1 import html
flashback,chemin=4,os.getcwd().replace('\\','/').split('OneDrive')[0]+'/OneDrive/Documents/private_life/Investissements/Donnees/BRVM/'
threshold,threshold_alt=.1,.01
tem=['ggplot2','gridon','none','plotly','plotly_dark','plotly_white','presentation','seaborn','simple_white','xgridoff','ygridoff']
temp,c=tem[rd.randint(0,len(tem)-1)],['rgb'+str(tuple(rd.randint(0,225) for i in range(3))) for i in range(7)]
def rn(x):
    try:
        return int(x)
    except:
        return 0
data=pd.read_excel('Cours_titres.xlsx')
for i in data.columns:
    if i=='Date/Société':
        data.loc[:,i]=data[i].apply(lambda x: pd.to_datetime(x,format="%Y-%m-%d"))
    else:
        data.loc[:,i]=data[i].apply(lambda x: rn(x))
dat,data1=data.copy(),data.copy()
data1['Date_Ord']=[i for i in range(len(data1))]
dat.loc[:,'Annee']=dat['Date/Société'].apply(lambda x: x.year)
ddllda={i:dat.loc[dat.Annee==i]['Date/Société'].iloc[0] for i in dat.Annee.unique()}
def bonn_div(x,rd,ad):
    try:
        return round(100*(-1+x[rd]/x[ad]),2)
    except:
        return 0
hdp=260# Horizon de prix
def monte_carlo_simulation(asset_prices,days=hdp,num_simulations=1000):
    try:
        asset_prices=asset_prices.replace(0,np.nan).dropna()
        log_returns=np.log(1+asset_prices.pct_change().dropna()).replace([np.inf,-np.inf],np.nan).dropna()# Calculer les rendements journaliers
        mu,sigma=log_returns.mean(),log_returns.std()# Moyenne et écart-type des rendements
        last_price=asset_prices.iloc[-1]# Dernier prix connu
        simulations=np.zeros((days,num_simulations))# Simulation des trajectoires
        simulations[0]=last_price
        for t in range(1,days):
            random_shocks=np.random.normal(mu,sigma,num_simulations)
            simulations[t]=simulations[t-1]*np.exp(random_shocks)
        return int(pd.DataFrame(simulations).dropna().mean(axis=1).iloc[-1])
    except:
        return 0
def random_walk(asset_prices,days=hdp):
    try:
        asset_prices=asset_prices.replace(0,np.nan).dropna()
        returns=(np.diff(asset_prices)/asset_prices[:-1]).replace([np.inf,-np.inf],np.nan).dropna()
        sigma=max(np.std(returns),.03)
        rw=[asset_prices.iloc[-1]]
        rw.append(rw[-1]*(1+np.clip(np.random.normal(0,sigma),-.075,.075)))
        return int(rw[-1])
    except:
        return 0
def black_scholes_simulation(asset_prices,days=hdp,num_simulations=1000):
    try:
        asset_prices=asset_prices.replace(0,np.nan).dropna()
        log_returns=np.log(asset_prices/asset_prices.shift(1)).replace([np.inf,-np.inf],np.nan).dropna()# rendements journaliers log-normaux
        mu,sigma=log_returns.mean(),log_returns.std()# Calculer le drift (rendement moyen) et la volatilité
        last_price=asset_prices.iloc[-1]# Dernier prix connu
        simulations=np.zeros((days,num_simulations))# Simulation des trajectoires de prix
        simulations[0]=last_price
        for t in range(1, days):
            epsilon=np.random.normal(0,1,num_simulations)
            simulations[t]=simulations[t-1]*np.exp((mu-.5*sigma**2)+sigma*epsilon)
        return int(pd.DataFrame(simulations).mean(axis=1).iloc[-1])
    except:
        return 0
def ap(x,met):
    if met=='Carlo':
        return monte_carlo_simulation(data[x])
    elif met=='Black':
        return black_scholes_simulation(data[x].astype(float).dropna())
    elif met=='Marche':
        return random_walk(data[x])
    else:
        return int((monte_carlo_simulation(data[x])+random_walk(data[x])+black_scholes_simulation(data[x].astype(float).dropna()))/3)
def best_predict(x):
    if abs(x.Carlo-x.Value)==min(abs(x.Carlo-x.Value),abs(x.Black-x.Value),abs(x.Marche-x.Value),abs(x.Moyenne-x.Value)):
        return 'Carlo',x.Carlo
    elif abs(x.Black-x.Value)==min(abs(x.Carlo-x.Value),abs(x.Black-x.Value),abs(x.Marche-x.Value),abs(x.Moyenne-x.Value)):
      return 'Black',x.Black
    elif abs(x.Marche-x.Value)==min(abs(x.Carlo-x.Value),abs(x.Black-x.Value),abs(x.Marche-x.Value),abs(x.Moyenne-x.Value)):
        return 'Marche',x.Marche
    else:
        return 'Moyenne',x.Moyenne
def best_next(data):
    if len(data)>hdp:
        ca=pd.DataFrame([[i] for i in data.columns[1:]],columns=['Titre'])
        ca.loc[:,'Last']=ca.Titre.apply(lambda x: data.head(-hdp)[x].iloc[-1])
        ca.loc[:,'Carlo']=ca.Titre.apply(lambda x: monte_carlo_simulation(data.head(-hdp)[x]))
        ca.loc[:,'Black']=ca.Titre.apply(lambda x: black_scholes_simulation(data.head(-hdp)[x].astype(float).dropna()))
        ca.loc[:,'Marche']=ca.Titre.apply(lambda x: random_walk(data.head(-hdp)[x]))
        ca.loc[:,'Moyenne']=ca.apply(lambda x: int((x.Carlo+x.Black+x.Marche)/3),axis=1)
        ca.loc[:,'Value']=ca.Titre.apply(lambda x: data[x].iloc[-1])
        ca.loc[:,'Best']=ca.apply(lambda x: best_predict(x)[0],axis=1)
        ca.loc[:,'Predict']=ca.apply(lambda x: best_predict(x)[1],axis=1)
        ca.loc[:,'Ecart']=ca.apply(lambda x: round(100*abs(x.Value-x.Predict)/abs(min(x.Value,x.Predict)))
                                   if abs(min(x.Value,x.Predict))!=0 else 0,axis=1)
        ca.loc[:,'Next']=ca.apply(lambda x: ap(x.Titre,x.Best),axis=1)
        ca.loc[:,'Variation']=ca.apply(lambda x: round(100*(-1+x.Next/x.Value)) if x.Value!=0 else 0,axis=1)
        ca['Last'],ca['Value']=ca.Last.apply(lambda x: int(x)),ca.Value.apply(lambda x: int(x))
        ca=ca.sort_values(by='Variation',ascending=False)
        ca=ca.rename(
            columns={'Last':'Valeur Année Précédente','Value':'Valeur Actuelle','Next':'Next Year','Variation':'Progression Estimée'})[
                ['Titre','Valeur Année Précédente','Valeur Actuelle','Next Year','Progression Estimée']]
        return ca
    else:
        ca=pd.DataFrame([[i] for i in data.columns[1:]],columns=['Titre'])
        ca.loc[:,'Last']=ca.Titre.apply(lambda x: data[x].iloc[0])
        ca.loc[:,'Carlo']=ca.Titre.apply(lambda x: monte_carlo_simulation(data[x]))
        ca.loc[:,'Black']=ca.Titre.apply(lambda x: black_scholes_simulation(data[x].astype(float).dropna()))
        ca.loc[:,'Marche']=ca.Titre.apply(lambda x: random_walk(data[x]))
        ca.loc[:,'Moyenne']=ca.apply(lambda x: int((x.Carlo+x.Black+x.Marche)/3),axis=1)
        ca.loc[:,'Value']=ca.Titre.apply(lambda x: data[x].iloc[-1])
        ca.loc[:,'Best']=ca.apply(lambda x: best_predict(x)[0],axis=1)
        ca.loc[:,'Predict']=ca.apply(lambda x: best_predict(x)[1],axis=1)
        ca.loc[:,'Ecart']=ca.apply(lambda x: round(100*abs(x.Value-x.Predict)/abs(min(x.Value,x.Predict)))
                                   if abs(min(x.Value,x.Predict))!=0 else 0,axis=1)
        ca.loc[:,'Next']=ca.apply(lambda x: ap(x.Titre,x.Best),axis=1)
        ca.loc[:,'Variation']=ca.apply(lambda x: round(100*(-1+x.Next/x.Value)) if x.Value!=0 else 0,axis=1)
        ca['Last'],ca['Value']=ca.Last.apply(lambda x: int(x)),ca.Value.apply(lambda x: int(x))
        ca=ca.sort_values(by='Variation',ascending=False)
        ca=ca.rename(
            columns={'Last':'Valeur Année Précédente','Value':'Valeur Actuelle','Next':'Next Year','Variation':'Progression Estimée'})[
                ['Titre','Valeur Année Précédente','Valeur Actuelle','Next Year','Progression Estimée']]
        return ca
def best_yearly(data,top):
    if len(data)>260:
        data=data.tail(rd.randint(259,261))
        co=data.loc[data['Date/Société']==data.iloc[0,0]].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'An_Dernier'},inplace=True)
    else:
        co=data.loc[data['Date/Société']==data.iloc[0,0]].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'An_Dernier'},inplace=True)
    ca=data.loc[data['Date/Société']==data.iloc[-1,0]].T.tail(data.shape[1]-1).reset_index()
    ca.rename(columns={'index':'Titre',ca.columns[1]:'Cette_Annee'},inplace=True)
    ca=ca.merge(co,on='Titre',how='left')
    ca['Cette_Annee'],ca['An_Dernier']=ca.Cette_Annee.apply(lambda x: int(x)),ca.An_Dernier.apply(lambda x: int(x))
    ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Cette_Annee','An_Dernier'),axis=1)
    ca=ca.sort_values(by='Variation',ascending=False).head(top)
    ca=ca.rename(columns={'Cette_Annee':'Valeur Actuelle','An_Dernier':'An Dernier','Variation':'Progression'})
    ca=ca[['Titre','An Dernier','Valeur Actuelle','Progression']]
    return ca
def best_monthly(data,top):
    if len(data)>25:
        data=data.tail(rd.randint(21,24))
        co=data.loc[data['Date/Société']==data.iloc[0,0]].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'Mois_Dernier'},inplace=True)
    else:
        co=data.loc[data['Date/Société']==data.iloc[0,0]].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'Mois_Dernier'},inplace=True)
    ca=data.loc[data['Date/Société']==data.iloc[-1,0]].T.tail(data.shape[1]-1).reset_index()
    ca.rename(columns={'index':'Titre',ca.columns[1]:'Today'},inplace=True)
    ca=ca.merge(co,on='Titre',how='left')
    ca['Today'],ca['Mois_Dernier']=ca.Today.apply(lambda x: int(x)),ca.Mois_Dernier.apply(lambda x: int(x))
    ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Today','Mois_Dernier'),axis=1)
    ca=ca.sort_values(by='Variation',ascending=False).head(top)
    ca=ca.rename(columns={'Today':'Valeur Actuelle','Mois_Dernier':'Last Month','Variation':'Progression'})
    ca=ca[['Titre','Last Month','Valeur Actuelle','Progression']]
    return ca
def best_hebdo(data,top):
    if len(data)>7:
        data=data.tail(6)
        co=data.loc[data['Date/Société']==data.iloc[0,0]].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'Semaine_Derniere'},inplace=True)
    else:
        co=data.loc[data['Date/Société']==data.iloc[0,0]].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'Semaine_Derniere'},inplace=True)
    ca=data.loc[data['Date/Société']==data.iloc[-1,0]].T.tail(data.shape[1]-1).reset_index()
    ca.rename(columns={'index':'Titre',ca.columns[1]:'Today'},inplace=True)
    ca=ca.merge(co,on='Titre',how='left')
    ca['Today'],ca['Semaine_Derniere']=ca.Today.apply(lambda x: int(x)),ca.Semaine_Derniere.apply(lambda x: int(x))
    ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Today','Semaine_Derniere'),axis=1)
    ca=ca.sort_values(by='Variation',ascending=False).head(top)
    ca=ca.rename(columns={'Today':'Valeur Actuelle','Semaine_Derniere':'Last Week','Variation':'Progression'})
    ca=ca[['Titre','Last Week','Valeur Actuelle','Progression']]
    return ca
predi,annee,mois,week=best_next(data),best_yearly(data,10),best_monthly(data,10),best_hebdo(data,10)
annee=annee.merge(predi[['Titre','Next Year','Progression Estimée']],on='Titre',how='left')
mois=mois.merge(predi[['Titre','Next Year','Progression Estimée']],on='Titre',how='left')
week=week.merge(predi[['Titre','Next Year','Progression Estimée']],on='Titre',how='left')
def secure_dataframe(df):
    html_code = f"""
    <div style="
        border: 1px solid #333;
        border-radius: 5px;
        padding: 10px;
        background: #1a1a1a;
        color: white;
        user-select: none;
        pointer-events: none;
    ">
        {df.to_html(index=False)}
    </div>
    <script>
        // Bloquer toute interaction
        document.querySelector('table').addEventListener('mousedown', e => e.preventDefault());
    </script>
    """
    return html(html_code)
st.title('Analyses des données de la BRVM')
choix=st.radio('Quelles données voulez vous afficher?',options=['📅 Meilleur hebdo','📅 Meilleur mensuel','📅 Meilleur annuel'],horizontal=True)
degr=['Accent','Accent_r','Blues','Blues_r','BrBG','BrBG_r','BuGn','BuGn_r','BuPu','BuPu_r','CMRmap','CMRmap_r','Dark2','Dark2_r','GnBu','GnBu_r','Grays','Greens',
      'Greens_r','Greys','Greys_r','OrRd','OrRd_r','Oranges','Oranges_r','PRGn','PRGn_r','Paired','Paired_r','Pastel1','Pastel1_r','Pastel2','Pastel2_r','PiYG',
      'PiYG_r','PuBu','PuBuGn','PuBuGn_r','PuBu_r','PuOr','PuOr_r','PuRd','PuRd_r','Purples','Purples_r','RdBu','RdBu_r','RdGy','RdGy_r','RdPu','RdPu_r','RdYlBu',
      'RdYlBu_r','RdYlGn','RdYlGn_r','Reds','Reds_r','Set1','Set1_r','Set2','Set2_r','Set3','Set3_r','Spectral','Spectral_r','Wistia','Wistia_r','YlGn','YlGnBu',
      'YlGnBu_r','YlGn_r','YlOrBr','YlOrBr_r','YlOrRd','YlOrRd_r','afmhot','afmhot_r','autumn','autumn_r','binary','binary_r','bone','bone_r','brg','brg_r','bwr',
      'bwr_r','cividis','cividis_r','cool','cool_r','coolwarm','coolwarm_r','copper','copper_r','cubehelix','cubehelix_r','flag','flag_r','gist_earth',
      'gist_earth_r','gist_gray','gist_gray_r','gist_grey','gist_heat','gist_heat_r','gist_ncar','gist_ncar_r','gist_rainbow','gist_rainbow_r','gist_stern',
      'gist_stern_r','gist_yarg','gist_yarg_r','gist_yerg','gnuplot','gnuplot2','gnuplot2_r','gnuplot_r','gray','gray_r','grey','hot','hot_r','hsv','hsv_r',
      'inferno','inferno_r','jet','jet_r','magma','magma_r','nipy_spectral','nipy_spectral_r','ocean','ocean_r','pink','pink_r','plasma','plasma_r','prism',
      'prism_r','rainbow','rainbow_r','seismic','seismic_r','spring','spring_r','summer','summer_r','tab10','tab10_r','tab20','tab20_r','tab20b','tab20b_r',
      'tab20c','tab20c_r','terrain','terrain_r','turbo','turbo_r','twilight','twilight_r','twilight_shifted','twilight_shifted_r','viridis','viridis_r','winter',
      'winter_r']
if choix=='📅 Meilleur annuel':
    if rd.randint(0,1)==1:
        annee=annee[annee.columns[:-2]]
    st.subheader('Top annuel')
    if rd.randint(0,1)==1:
        st.dataframe(annee.style.set_properties(**{'background-color': 'black','color': 'white','border': '1px solid grey'}).format(
            {'Progression': '{:.1f}%','Progression Estimée': '{:.1f}%'},precision=1).set_table_styles(
                [{'selector': 'th','props': [('font-size', '14px')]}]).background_gradient(
                cmap=rd.choice(degr)).set_properties(subset=pd.IndexSlice[::2, :], **{'border-bottom': '2px solid white'}))
    else:
        secure_dataframe(annee.style.set_properties(**{'background-color': 'black','color': 'white','border': '1px solid grey'}).format(
            {'Progression': '{:.1f}%','Progression Estimée': '{:.1f}%'},precision=1).set_table_styles(
                [{'selector': 'th','props': [('font-size', '14px')]}]).background_gradient(
                cmap=rd.choice(degr)).set_properties(subset=pd.IndexSlice[::2, :], **{'border-bottom': '2px solid white'}))
elif choix=='📅 Meilleur mensuel':
    if rd.randint(0,1)==1:
        mois=mois[mois.columns[:-2]]
    st.subheader('Top mensuel')
    if rd.randint(0,1)==1:
        st.dataframe(mois.style.set_properties(**{'background-color': 'black','color': 'white','border': '1px solid grey'}).format(
            {'Progression': '{:.1f}%','Progression Estimée': '{:.1f}%'},precision=1).set_table_styles(
                [{'selector': 'th','props': [('font-size', '14px')]}]).background_gradient(
                cmap=rd.choice(degr)).set_properties(subset=pd.IndexSlice[::2, :], **{'border-bottom': '2px solid white'}))
    else:
        secure_dataframe(mois.style.set_properties(**{'background-color': 'black','color': 'white','border': '1px solid grey'}).format(
            {'Progression': '{:.1f}%','Progression Estimée': '{:.1f}%'},precision=1).set_table_styles(
                [{'selector': 'th','props': [('font-size', '14px')]}]).background_gradient(
                cmap=rd.choice(degr)).set_properties(subset=pd.IndexSlice[::2, :], **{'border-bottom': '2px solid white'}))
elif choix=='📅 Meilleur hebdo':
    if rd.randint(0,1)==1:
        week=week[week.columns[:-2]]
    st.subheader('Top hebdomadaire')
    if rd.randint(0,1)==1:
        st.dataframe(week.style.set_properties(**{'background-color': 'black','color': 'white','border': '1px solid grey'}).format(
            {'Progression': '{:.1f}%','Progression Estimée': '{:.1f}%'},precision=1).set_table_styles(
                [{'selector': 'th','props': [('font-size', '14px')]}]).background_gradient(
                cmap=rd.choice(degr)).set_properties(subset=pd.IndexSlice[::2, :], **{'border-bottom': '2px solid white'}))
    else:
        secure_dataframe(week.style.set_properties(**{'background-color': 'black','color': 'white','border': '1px solid grey'}).format(
            {'Progression': '{:.1f}%','Progression Estimée': '{:.1f}%'},precision=1).set_table_styles(
                [{'selector': 'th','props': [('font-size', '14px')]}]).background_gradient(
                cmap=rd.choice(degr)).set_properties(subset=pd.IndexSlice[::2, :], **{'border-bottom': '2px solid white'}))
ndj=rd.randint(10,len(data))
ddr=data.tail(ndj)['Date/Société'].iloc[0]
#rep=pd.DataFrame([[ddr,bst_ptf(ndj)[0],bst_ptf(ndj)[1]]],columns=['Historique','Actif','Rendement'])
co=data.loc[data['Date/Société']==ddr].T.tail(data.shape[1]-1).reset_index()# Progression depuis la date de référence
co.rename(columns={'index':'Titre',co.columns[1]:'Date_Reference'},inplace=True)
ca=data.loc[data['Date/Société']==data.iloc[-1,0]].T.tail(data.shape[1]-1).reset_index()
ca.rename(columns={'index':'Titre',ca.columns[1]:'Today'},inplace=True)
ca=ca.merge(co,on='Titre',how='left')
ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Today','Date_Reference'),axis=1)
ca.sort_values(by='Variation',ascending=False,inplace=True)
#print(ca.head(10).Variation.mean(),ca.head().Variation.mean())
#print('10 des plus extrêmes performances depuis le',str(ddr)[:-9],'\n',pd.concat([ca.head(),ca.tail()]),'\n')
mpdr,ppdr=(ca.Titre.iloc[0],str(round(ca.Variation.iloc[0],2))+'%'),(ca.Titre.iloc[-1],str(round(ca.Variation.iloc[-1],2))+'%')
try:#Performances Annuelles
    co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(365)].T.tail(data.shape[1]-1).reset_index()
    co.rename(columns={'index':'Titre',co.columns[1]:'An_Dernier'},inplace=True)
except:
    try:
        co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(366)].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'An_Dernier'},inplace=True)
    except:
        co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(364)].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'An_Dernier'},inplace=True)
ca=data.loc[data['Date/Société']==data.iloc[-1,0]].T.tail(data.shape[1]-1).reset_index()
ca.rename(columns={'index':'Titre',ca.columns[1]:'Cette_Annee'},inplace=True)
ca=ca.merge(co,on='Titre',how='left')
ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Cette_Annee','An_Dernier'),axis=1)
ca.sort_values(by='Variation',ascending=False,inplace=True)
#print(ca.head(10).Variation.mean(),ca.head().Variation.mean())
#print('10 des plus extrêmes peformances annuelles\n',pd.concat([ca.head(),ca.tail()]),'\n')
mpa,ppa=(ca.Titre.iloc[0],str(round(ca.Variation.iloc[0],2))+'%'),(ca.Titre.iloc[-1],str(round(ca.Variation.iloc[-1],2))+'%')
sta1=np.log(data[data.columns[1:]]/data[data.columns[1:]].shift(1)).dropna().std().dropna()
st1=sta1.reset_index().tail(data.shape[1]-1).rename(columns={'index':'Titre',0:'Ecart_Type'}).sort_values(by='Ecart_Type')
st1=st1.loc[st1.Ecart_Type>0]
st1['Rang']=[i+1 for i in range(len(st1))]
st1['Constat']=st1.Rang.apply(lambda x: 'Stable' if x<len(st1)/2 else 'Instable')
try:#Perfomances Mensuelles
    co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(30)].T.tail(data.shape[1]-1).reset_index()
    co.rename(columns={'index':'Titre',co.columns[1]:'Mois_Dernier'},inplace=True)
except:
    try:
        co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(31)].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'Mois_Dernier'},inplace=True)
    except:
        co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(29)].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'Mois_Dernier'},inplace=True)
ca=data.loc[data['Date/Société']==data.iloc[-1,0]].T.tail(data.shape[1]-1).reset_index()
ca.rename(columns={'index':'Titre',ca.columns[1]:'Today'},inplace=True)
ca=ca.merge(co,on='Titre',how='left')
ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Today','Mois_Dernier'),axis=1)
ca.sort_values(by='Variation',ascending=False,inplace=True)
mpm,ppm=(ca.Titre.iloc[0],str(round(ca.Variation.iloc[0],2))+'%'),(ca.Titre.iloc[-1],str(round(ca.Variation.iloc[-1],2))+'%')
try:
    co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(7)].T.tail(data.shape[1]-1).reset_index()#Peformances Hebdomadaires
    co.rename(columns={'index':'Titre',co.columns[1]:'Semaine_Derniere'},inplace=True)
except:
    co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(8)].T.tail(data.shape[1]-1).reset_index()#Peformances Hebdomadaires
    co.rename(columns={'index':'Titre',co.columns[1]:'Semaine_Derniere'},inplace=True)
ca=data.loc[data['Date/Société']==data.iloc[-1,0]].T.tail(data.shape[1]-1).reset_index()
ca.rename(columns={'index':'Titre',ca.columns[1]:'Today'},inplace=True)
ca=ca.merge(co,on='Titre',how='left')
ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Today','Semaine_Derniere'),axis=1)
ca.sort_values(by='Variation',ascending=False,inplace=True)
mph,pph=(ca.Titre.iloc[0],str(round(ca.Variation.iloc[0],2))+'%'),(ca.Titre.iloc[-1],str(round(ca.Variation.iloc[-1],2))+'%')
try:#Performances Journalières
    co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(1)].T.tail(data.shape[1]-1).reset_index()
    co.rename(columns={'index':'Titre',co.columns[1]:'Veille'},inplace=True)
except:
    try:
        co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(2)].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'Veille'},inplace=True)
    except:
        co=data.loc[data['Date/Société']==data.iloc[-1,0]-dt.timedelta(3)].T.tail(data.shape[1]-1).reset_index()
        co.rename(columns={'index':'Titre',co.columns[1]:'Veille'},inplace=True)
ca=data.loc[data['Date/Société']==data.iloc[-1,0]].T.tail(data.shape[1]-1).reset_index()
ca.rename(columns={'index':'Titre',ca.columns[1]:'Today'},inplace=True)
ca=ca.merge(co,on='Titre',how='left')
ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Today','Veille'),axis=1)
ca.sort_values(by='Variation',ascending=False,inplace=True)
mpj,ppj=(ca.Titre.iloc[0],str(round(ca.Variation.iloc[0],2))+'%'),(ca.Titre.iloc[-1],str(round(ca.Variation.iloc[-1],2))+'%')
ca=pd.DataFrame([[i] for i in data.columns[1:]],columns=['Titre'])
ca.loc[:,'Last']=ca.Titre.apply(lambda x: data.head(-hdp)[x].iloc[-1])
ca.loc[:,'Carlo']=ca.Titre.apply(lambda x: monte_carlo_simulation(data.head(-hdp)[x]))
ca.loc[:,'Black']=ca.Titre.apply(lambda x: black_scholes_simulation(data.head(-hdp)[x].astype(float).dropna()))
ca.loc[:,'Marche']=ca.Titre.apply(lambda x: random_walk(data.head(-hdp)[x]))
ca.loc[:,'Moyenne']=ca.apply(lambda x: int((x.Carlo+x.Black+x.Marche)/3),axis=1)
ca.loc[:,'Value']=ca.Titre.apply(lambda x: data[x].iloc[-1])
ca.loc[:,'Best']=ca.apply(lambda x: best_predict(x)[0],axis=1)
ca.loc[:,'Predict']=ca.apply(lambda x: best_predict(x)[1],axis=1)
ca.loc[:,'Ecart']=ca.apply(lambda x: round(100*abs(x.Value-x.Predict)/abs(min(x.Value,x.Predict)))
                           if abs(min(x.Value,x.Predict))!=0 else 0,axis=1)
ca.loc[:,'Next']=ca.apply(lambda x: ap(x.Titre,x.Best),axis=1)
ca.loc[:,'Variation']=ca.apply(lambda x: round(100*(-1+x.Next/x.Value)),axis=1)
#ca.loc[:,'Variation']=ca.apply(lambda x: bonn_div(x,'Next','Value'),axis=1)
ca=ca[['Titre','Last','Value','Best','Predict','Ecart','Next','Variation']].sort_values(by='Variation',ascending=False)
me,pe=(ca.Titre.iloc[0],str(int(ca.Variation.iloc[0]))+'%',ca.Next.iloc[0]),(ca.Titre.iloc[-1],str(int(ca.Variation.iloc[-1]))+'%',ca.Next.iloc[-1])
def tddb():
    return pd.DataFrame([['Meilleure Estimation +'+str(me[1])+' à '+str(me[2]),[me[0]]],['Pire Estimation '+str(pe[1])+' à '+str(pe[2]),[pe[0]]],
                         ["Volatile",[st1.Titre.iloc[-1]]],["Stable",[st1.Titre.iloc[0]]],["Reference "+str(ddr)[:-9]+'+'+str(mpdr[1]),[mpdr[0]]],
                         ["Reference "+str(ddr)[:-9]+' '+str(ppdr[1]),[ppdr[0]]],["Annuel+"+str(mpa[1]),[mpa[0]]],["Annuel "+str(ppa[1]),[ppa[0]]],
                         ["Mensuel+"+str(mpm[1]),[mpm[0]]],["Mensuel "+str(ppm[1]),[ppm[0]]],["Hebdo+"+str(mph[1]),[mph[0]]],
                         ["Hebdo "+str(pph[1]),[pph[0]]],["Jour+"+str(mpj[1]),[mpj[0]]],["Jour "+str(ppj[1]),[ppj[0]]]],columns=['Constat','Titres'])
d,l=tddb(),[]
for i in range(len(d)):
    try:
        l.append(d.iloc[i,1][0])
    except:
        l+=d.iloc[i,1]
l=list(set(l))
def nda(x):
    it=0
    for i in range(len(d)):
        if x in d.iloc[i,1]:
            it-=-1
    return it
def real(x):
    res=''
    for i in range(len(d)):
        if x in d.iloc[i,1]:
            if res=='':
                res+=d.iloc[i,0]
            else:
                res+='/'+d.iloc[i,0]
    return res
perf=pd.DataFrame([[i,real(i)] for i in l],columns=['Titres','Constat']).sort_values(by='Constat')
def ajout(debut,aajouter):
    if debut=='':
        debut+=aajouter
    else:
        debut+=' | '+aajouter
    return debut
def stabilite(donn,delai_vol=50):
    cro=np.log(donn[donn.columns[1:]].tail(delai_vol)/donn[donn.columns[1:]].tail(delai_vol).shift(1)).fillna(0)
    sta1=cro.std().fillna(0)
    st1=sta1.reset_index().tail(donn.shape[1]-1).rename(columns={'index':'Titre',0:'Ecart_Type'}).sort_values(by='Ecart_Type')
    st1=st1.loc[st1.Ecart_Type>0]
    st1['Rang']=[i+1 for i in range(len(st1))]
    st1['Constat']=st1.Rang.apply(lambda x: 'Stable' if x<len(st1)/2 else 'Instable')
    return st1.loc[st1.Constat=='Stable'].Titre.unique(),cro
def commentaires(donn,titre,modele,arriere=flashback,affiche2='Non'):
    com=''
    ct,mt,lt,delai=len(donn)//3,2*len(donn)//3,3*len(donn)//3,len(donn)//5
    dernier_prix,prix_max,prix_min,court_terme=donn[titre].iloc[-1],donn[titre].max(),donn[titre].min(),donn[titre].iloc[-ct:].mean()
    max_local,min_local,min_lague=donn[titre].iloc[-delai:].max(),donn[titre].iloc[-delai:].min(),donn[titre].iloc[-1-flashback:].min()
    moyen_terme,long_terme,max_lague=donn[titre].iloc[-mt:-ct].mean(),donn[titre].iloc[-lt:-mt].mean(),donn[titre].iloc[-1-flashback:].max()
    if dernier_prix==prix_max:
        com=ajout(com,'Sommet Historique')
    elif dernier_prix==max_local:
        com=ajout(com,'Sommet Local')
    if dernier_prix==prix_min:
        com=ajout(com,'Vallée Historique')
    elif dernier_prix==min_local:
        com=ajout(com,'Vallée Locale')
    if court_terme<moyen_terme<long_terme:
        com=ajout(com,'Tendance baissière')
    elif moyen_terme>max(court_terme,long_terme):
        com=ajout(com,'Courbure baissière')
    if court_terme>moyen_terme>long_terme:
        com=ajout(com,'Tendance haussière')
    elif moyen_terme<min(court_terme,long_terme):
        com=ajout(com,'Courbure haussière')
    try:
        st,cro=stabilite(donn,len(donn))
        if titre in st:
            com=ajout(com,'Titre Stable')
        else:
            com=ajout(com,'Titre Instable')
        if titre in st[:3]:
            com=ajout(com,'Forte Stabilité')
        if len([i for i in range(arriere) if cro[titre].iloc[-1-i]>=0])==arriere:
            com=ajout(com,'Croissance Soutenue')
        if dernier_prix/min_lague>1+max(threshold,threshold_alt):
            com=ajout(com,'Hausse')
        if dernier_prix/max_lague<1-min(threshold,threshold_alt) and not 'baissière' in com:
            com=ajout(com,'Baisse')
    except:
        pass
    if modele=='Modele1':
        if 'Croissance' in com and 'Hausse' in com and ('Tendance haussière' in com or 'Stable' in com):
            com=ajout(com,'Achat Favorable')
        elif 'baiss' in com.lower() and 'Instable' in com:
            com=ajout(com,'Vente Favorable')
    if affiche2=='Oui':
        print({'Dernier prix':dernier_prix,'Max hitorique':prix_max,'Min historique':prix_min,'Max local':max_local,'Min local':min_local,
               'Court terme':court_terme,'Moyen terme':moyen_terme,'Long terme':long_terme,'Borne inf':1-threshold_alt,'Borne max':1+threshold_alt,
               'Ratio max':max(court_terme,moyen_terme,long_terme)/min(court_terme,moyen_terme,long_terme),
               'Ratio min':min(court_terme,moyen_terme,long_terme)/max(court_terme,moyen_terme,long_terme)})
    return com
def graphique(data,titre,modele,perf=perf):
    data=data.loc[data[titre]>0]
    data=data1.loc[data1['Date/Société'].isin(data['Date/Société'])]
    if len(data)>0:
        if titre in perf.Titres.unique():
            tit=perf.loc[perf.Titres==titre].Constat.iloc[0]+' '+commentaires(data,titre,modele)
            if len(tit.split(' | '))<4:
                fig=px.line(data,x='Date/Société',y=titre,color_discrete_sequence=c,template=temp,markers=rd.choice([True,False]),
                        line_shape=rd.choice(['hv','hvh','linear','vh','vhv']),title=tit)
            else:
                print(tit)
                fig=px.line(data,x='Date/Société',y=titre,color_discrete_sequence=c,template=temp,markers=rd.choice([True,False]),
                        line_shape=rd.choice(['hv','hvh','linear','vh','vhv']))
        else:
            tit=commentaires(data,titre,modele)
            if len(tit.split(' | '))<4:
                fig=px.line(data,x='Date/Société',y=titre,color_discrete_sequence=c,template=temp,markers=rd.choice([True,False]),
                        line_shape=rd.choice(['hv','hvh','linear','vh','vhv']),title=tit)
            else:
                print(tit)
                fig=px.line(data,x='Date/Société',y=titre,color_discrete_sequence=c,template=temp,markers=rd.choice([True,False]),
                        line_shape=rd.choice(['hv','hvh','linear','vh','vhv']))
        fig.update_traces(line_width=2.5,hovertemplate='%{y:f} FCFA<br>%{x|%d %b %Y}')
        return fig
if rd.randint(0,1)==0:
    d1=rd.choice(data.loc[data['Date/Société']>dt.datetime(2022,12,1)]['Date/Société'].unique())
    d2=rd.choice(data.loc[data['Date/Société']>dt.datetime(2022,12,1)]['Date/Société'].unique())
else:
    d1,d2=rd.choice(data['Date/Société'].unique()),rd.choice(data['Date/Société'].unique())
def secure_plotly_figure(fig):
    # Désactive le modebar (contient le bouton de téléchargement)
    fig.update_layout(modebar_remove=['toImage', 'select2d', 'lasso2d'],dragmode=False)
    # Ajoute un filigrane dynamique
    fig.add_annotation(text=rd.choice([f"{dt.datetime.today()}","Cédric K. N'ZI"]),opacity=0.2,font=dict(color=rd.choice(['blue','green',"red"]), size=40),
                       xref="paper", yref="paper",x=0.5,y=0.5,showarrow=False)
    return fig
st.markdown("""
<style>
/* Désactive la sélection de texte */
.plotly-notifier, .modebar-container { 
    user-select: none; 
    -webkit-user-select: none;
}

/* Watermark CSS supplémentaire */
.plot-container {
    position: relative;
}

.plot-container::after {
    content: "Copyright © 2024";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: rgba(255,0,0,0.15);
    font-size: 40px;
    pointer-events: none;
}
</style>

<script>
// Bloque le clic droit sur tout le document
document.addEventListener('contextmenu', event => {
    if (event.target.closest('.plotly-graph-div')) {
        event.preventDefault();
        alert('Capture d\'écran interdite !');
    }
});
</script>
""", unsafe_allow_html=True)
st.title('Graphiques des titres de la BRVM')
choix=st.radio('Quel titre voulez vous visualiser?',options=list(data.columns[1:]),horizontal=True)
if rd.randint(0,1)==0:
    secured_fig=secure_plotly_figure(graphique(data.loc[data['Date/Société']>=min(d1,d2)],choix,'Modele1'))
    st.plotly_chart(secured_fig, config={'displayModeBar': True,  # Garde la barre d'outils mais sans bouton export
                                         'modeBarButtonsToRemove': ['toImage', 'select2d', 'lasso2d'],'scrollZoom': False})
else:
    fig=graphique(data.loc[data['Date/Société']>=min(d1,d2)],choix,'Modele1')
    st.plotly_chart(fig)
