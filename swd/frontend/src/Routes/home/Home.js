
/* eslint no-unused-vars:0 */

import React from 'react';
import PropTypes from 'prop-types';
import { Card, CardActions, CardHeader, CardMedia, CardTitle, CardText } from 'material-ui/Card';
import { Mobile } from '../../Components/Responsive';
import InfoCard from '../../Components/InfoCard';
import background from './Background.svg';
import bdome from './BDome.svg';
import s from './Home.css';
import { gql, graphql } from 'react-apollo'

const query = gql`
{
  currentUser {
    id
    username
  }
}
`

class Home extends React.Component {
  static propTypes = {
    news: PropTypes.arrayOf(PropTypes.shape({
      title: PropTypes.string.isRequired,
      link: PropTypes.string.isRequired,
      content: PropTypes.string,
    })).isRequired,
    data: PropTypes.arrayOf(PropTypes.shape({
      loading: React.PropTypes.bool,
      error: React.PropTypes.object,
      currentUser: React.PropTypes.object,
    })).isRequired,
  };
    
  // const data = (props) => {
  //   const loading = props.data.loading;
  //   const error = props.data.error;
  //   const currentUser = props.data.currentUser;
  //   // render UI with loading, error, or currentUser
  // }


  render() {
    return (
      <Mobile>
        <div className={s.container} style={{ backgroundImage: `url(${background})` }}>
          <Card>
            <CardMedia>
              <img src={bdome} style={{ maxWidth: '80%' }} alt="SWD" />

            </CardMedia>
          </Card>
          <InfoCard title="Latest News" list={this.props.news} />
          <div>{this.props.data.currentUser.username}</div> 
        </div>
      </Mobile>

    );
  }
}

Home = graphql(query)(Home)

export default Home;