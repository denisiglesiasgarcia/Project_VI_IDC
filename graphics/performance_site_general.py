import os
import datetime
from pathlib import PureWindowsPath
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FixedLocator

def performance_site_general(df, liste_sites):
    now = datetime.datetime.now()
    date_png = str(now.strftime("%Y-%m-%d"))
    date_titre = str(now.strftime("%d-%m-%Y"))
    # Create a new directory with the current date as its name
    today = datetime.datetime.today()
    DIRECTORY = os.path.join('01_graphiques\\02_performance_sites_general\\', today.strftime("%Y-%m-%d"))
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)
    
    def df_site(site):
        # filtrer les données selon besoins
        bar_data = df_analyse_bars[df_analyse_bars['Nom_projet'] == site]
        bar_data = bar_data.drop(columns=['statut'])
        # bar_data = df_analyse_bars[~df_analyse_bars['IDC moy 3 ans avant [MJ/m²]'].isnull()]

        # stack pour adapter les données pour le graphique
        # https://stackoverflow.com/questions/66998010/how-to-pivot-from-columns-to-rows-in-pandas
        bar_data = bar_data.set_index (['Nom_projet'])
        bar_data = bar_data.stack().rename_axis (['Nom_projet','Type']).reset_index()
        bar_data.rename(columns={0: 'Valeur'},inplace=True)

        # Séparer les données pour le graphique
        bar_data1 = bar_data[(bar_data['Type'] != 'Part atteinte des objectifs [%]')]
        bar_data1 = bar_data1[(bar_data1['Type'] != 'Baisse IDC réalisée')]
        bar_data1 = bar_data1[(bar_data1['Type'] != 'Baisse IDC visée')]

        bar_data2 = bar_data[(bar_data['Type'] == 'Part atteinte des objectifs [%]')]

        try:
            # https://stackoverflow.com/questions/21923524/extracting-single-value-from-column-in-pandas
            perf_atteinte = bar_data2['Valeur'].values[bar_data2['Type'] == 'Part atteinte des objectifs [%]']
            perf_atteinte = int (perf_atteinte * 100)

            bar_data.sort_values(by=['Type'])
            return bar_data1, bar_data2, perf_atteinte
        except:
            return bar_data1, bar_data2

    # Préparer les données pour le graphique
    df_analyse = df.copy()

    df_analyse_bars = df_analyse[['Nom_projet','statut',
                            'Ef,avant,corr (IDC_avant) [MJ/m²]',
                            'Ef,obj*fp (Objectif en EF pondérée après) [MJ/m²]',
                            'Ef,après,corr*fp (Conso. mesurée après) [MJ/m²]',
                            'Part atteinte des objectifs [%]']].copy()
    df_analyse_bars['Baisse IDC visée'] = df_analyse_bars.loc[:, 'Ef,avant,corr (IDC_avant) [MJ/m²]'] \
        - df_analyse_bars.loc[:, 'Ef,obj*fp (Objectif en EF pondérée après) [MJ/m²]']
    df_analyse_bars['Baisse IDC réalisée'] = df_analyse_bars.loc[:, 'Ef,avant,corr (IDC_avant) [MJ/m²]'] \
        - df_analyse_bars.loc[:, 'Ef,après,corr*fp (Conso. mesurée après) [MJ/m²]']


    df_analyse_bars.rename (columns={'Ef,avant,corr (IDC_avant) [MJ/m²]': 'IDC moy3ans avant',
                                'Ef,obj*fp (Objectif en EF pondérée après) [MJ/m²]': 'Objectif',
                                'Ef,après,corr*fp (Conso. mesurée après) [MJ/m²]': 'Conso mesurée'
                                },inplace=True)
    df_analyse_bars.fillna(0)

    # Temps exploitation
    this_year = int(datetime.datetime.now().year)
    df_analyse['fin_travaux'] = pd.to_datetime(df_analyse['fin_travaux'], errors='coerce')
    df_analyse['fin_travaux'] = df_analyse['fin_travaux'].dt.year
    df_analyse['fin_travaux'] = df_analyse['fin_travaux'].fillna(np.nan)
    df_analyse['fin_travaux'] = df_analyse['fin_travaux'].fillna(0)
    df_analyse['fin_travaux'] = df_analyse['fin_travaux'].astype(int)
    df_analyse['finalise_depuis'] = this_year - df_analyse['fin_travaux']
    df_analyse.loc[df_analyse['fin_travaux'] == 0, 'finalise_depuis'] = -1
    df_analyse['finalise_depuis'] = df_analyse['finalise_depuis'].replace({
        -1: "(Travaux pas\n finalisés)\n\n",
        0: "(1ère année\nd'exploitation)\n\n",
        1: "(1ère année\nd'exploitation)\n\n",
        2: "(2ème année\nd'exploitation)\n\n",
        3: "(2ème année\nd'exploitation)\n\n",
        4: "(3ème année\nd'exploitation)\n\n",
        5: "(3ème année\nd'exploitation)\n\n",
    })

    # Graphique

    # texte pour les x du graphique
    liste_sites_reduit = []
    for liste_site in liste_sites:
        # nettoyer les noms de sites
        if '_' in liste_site:
            liste_site_reduit_string = liste_site.split('_')[0]
        
        else:
            liste_site_reduit_string = liste_site
        
        # statut
        if df_analyse[df_analyse['Nom_projet'] == liste_site]['statut'].values[0] == 'Terminé':
            liste_site_reduit_string = liste_site_reduit_string + \
                '\n(' + str(df_analyse[df_analyse['Nom_projet'] == liste_site]['statut'].values[0]) + ')'

        if df_analyse[df_analyse['Nom_projet'] == liste_site]['statut'].values[0] != 'Terminé':
            liste_site_reduit_string = liste_site_reduit_string + \
                                        '\n' + \
                                        str(df_analyse[df_analyse['Nom_projet'] == liste_site]['finalise_depuis'].values[0])

        liste_sites_reduit.append(liste_site_reduit_string)

    # pandas concat multiple dataframes
    df_analyse_sites_list = []
    for site in liste_sites:
        df_analyse_sites_list.append(df_site(site)[0])
    df_analyse_sites = pd.concat(df_analyse_sites_list, axis=0, ignore_index=True)

    # Graphique
    cm = 1 / 2.54
    sns.set(style="white",rc={"figure.figsize":(47* cm, 15 * cm)})
    
    # barplot
    fig = sns.barplot(x="Nom_projet", y="Valeur", hue="Type", data=df_analyse_sites, palette="Set2")
    locs = np.arange(len(liste_sites_reduit))
    fig.xaxis.set_major_locator(FixedLocator(locs))
    fig.set_xticklabels(liste_sites_reduit, rotation=0, horizontalalignment='center')

    # remove 
    sns.despine()
    fig.set(xlabel=None)

    # get yticks and append 150 and 250
    y_ticks = fig.get_yticks()
    y_ticks = np.append(y_ticks, 150)
    y_ticks = np.append(y_ticks, 250)
    fig.set_yticks(y_ticks)

    # value over bars
    for p in fig.patches:
        fig.annotate(format(p.get_height(), '.0f'),
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 5),
                    textcoords='offset points',
                    fontsize=8)
    # perf sur les x
    position_text_y = -160 # modifier hauteur ici
    for i in fig.get_xticks():
        text_perf_val = df_analyse[df_analyse['Nom_projet'] == liste_sites[i]]['Part atteinte des objectifs [%]'].values[0]
        if text_perf_val < 0.80:
            edgecolor = 'orange'
            facecolor = 'bisque'
        else:
            edgecolor = 'green'
            facecolor = 'lightgreen'
        text_perf = str(round(text_perf_val*100,1)) + '%'
        fig.text(i, position_text_y, text_perf, transform=fig.transData,
            ha='center', va='top',
            bbox=dict(facecolor=facecolor, edgecolor=edgecolor, boxstyle='round,pad=0.2'))

    # annotations performances
    HAUTEUR_TEXTE1 = -0.29 # modifier hauteur ici
    HAUTEUR_TEXTE2 = HAUTEUR_TEXTE1 - 0.05
    HAUTEUR_TEXTE3 = HAUTEUR_TEXTE2 - 0.07
    HAUTEUR_TEXTE4 = HAUTEUR_TEXTE3 - 0.02

    moyenne_performances_exploitation = round((df_analyse[df_analyse['Nom_projet'].isin(liste_sites) & 
                                            (df_analyse['Part atteinte des objectifs [%]'] != 0) & 
                                            (df_analyse['statut'] != 'Terminé')
                                            ]['Part atteinte des objectifs [%]'].mean())*100, 1)
    moyenne_performances_exploitation_str = 'Performances moyennes atteintes (sites en exploitation) : ' + str(moyenne_performances_exploitation) + '%'
    r = fig.text(0, HAUTEUR_TEXTE1, moyenne_performances_exploitation_str, transform=fig.transAxes,
                ha="left", va="center", rotation=0, size=11,
                bbox=dict(boxstyle="square,pad=0.1",
                        fc="lightgreen", lw=2))

    TEXT_COMPARE_RENOVE1 = "Etude Compare-Rénove*: "
    s = fig.text(0, HAUTEUR_TEXTE2, TEXT_COMPARE_RENOVE1, transform=fig.transAxes,
                ha="left", va="center", rotation=0, size=10)
    TEXT_COMPARE_RENOVE2 = "42% "
    s = fig.text(0.14, HAUTEUR_TEXTE2, TEXT_COMPARE_RENOVE2, transform=fig.transAxes,
                ha="left", va="center", rotation=0, size=10, color='red')
    TEXT_COMPARE_RENOVE3 = "en moyenne "
    s = fig.text(0.17, HAUTEUR_TEXTE2, TEXT_COMPARE_RENOVE3, transform=fig.transAxes,
                ha="left", va="center", rotation=0, size=10)

    TEXT_COMPARE_RENOVE_SOURCE = "* Source: «COMPARE RENOVE : du catalogue de solutions à la performance réelle" +\
                            "des rénovations énergétiques»,\nauteurs: Khoury Jad, Hollmuller Pierre, Lachal Bernard Marie," +\
                            "Schneider Stefan et Lehmann Ursula."
    t = fig.text(0, HAUTEUR_TEXTE3, TEXT_COMPARE_RENOVE_SOURCE, transform=fig.transAxes,
                ha="left", va="center", rotation=0, size=8)

    # date de génération du graphique
    now = datetime.datetime.now()
    date_str = 'Selon données disponible au: ' + str(now.strftime("%d-%m-%Y"))
    u = fig.text(0.82, HAUTEUR_TEXTE4, date_str, transform=fig.transAxes, 
                ha='left', va='bottom', fontsize=8)

    # titres
    # get the current date format d/m/y
    now = datetime.datetime.now()
    date = str(now.strftime("%d-%m-%Y"))
    fig.set_title("Performances des premiers projets AMOén", fontsize=14, fontweight='bold')
    # remove xlabel set_xlabel
    
    #fig.set_xlabel("Projets AMOén")
    fig.set_ylabel("IDC [MJ/m²/an]")
    plt.subplots_adjust(bottom=0.3, right=0.82, left=0.05, top=0.95)

    # légende
    #sns.move_legend(fig, "upper left", bbox_to_anchor=(1, 1))
    #fig.legend(loc='best', ncol=3)
    #get handles and labels
    handles, labels = plt.gca().get_legend_handles_labels()
    #specify order of items in legend
    order = [0,1,2]

    #add legend to plot
    plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order], bbox_to_anchor=(1,1), loc="upper right")

    # Sauvegarder graphique
    sauvegarde_png = os.path.join(DIRECTORY, "02_performance_sites_general-" + date_png + '.png')
    #sauvegarde_png = '01_graphiques\\' + sauvegarde_png + "-" + date + '.png' 
    plt.savefig(sauvegarde_png, dpi=600)

    #plt.show()
    plt.close()
    return sauvegarde_png